# File: rag_retrieval.py
# 實現 RAG 檢索，結合 Ollama 的 Qwen3 0.6B，支援連續對話點餐，訂單狀態由程式管理
import json
import ollama
from langchain_chroma import Chroma  # 使用新套件
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import torch
import re

# 初始化嵌入模型（用於向量檢索）
try:
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    print(f"嵌入模型載入失敗：{e}")
    raise e

# 從 Chroma 載入向量資料庫
def load_menu_to_vectorstore(persist_directory="./chroma_db"):
    try:
        vectorstore = Chroma(
            collection_name="mcdonalds_menu",
            embedding_function=embedding_model,
            persist_directory=persist_directory
        )
        print("向量資料庫載入成功")
        return vectorstore
    except Exception as e:
        print(f"Chroma 資料庫載入失敗：{e}")
        print("請確認 ./chroma_db 存在，或重新跑 load_menu_to_chroma.py 生成資料庫")
        raise e

# 解析用戶輸入，更新訂單狀態（不依賴 LLM）
def parse_user_input(query, docs, order_state):
    query = query.lower().strip()
    intent = "unknown"
    item_info = None
    customizations = []

    # 定義關鍵詞
    cancel_keywords = ["不要", "取消", "移除"]
    customize_keywords = ["無鹽", "去冰", "少冰", "加糖", "無糖"]
    confirm_keywords = ["確認", "結帳", "完成"]
    end_keywords = ["結束", "不用了", "謝謝"]
    size_keywords = ["中", "大", "小"]

    # 檢查意圖
    if any(kw in query for kw in confirm_keywords):
        intent = "confirm"
    elif any(kw in query for kw in end_keywords):
        intent = "end"
    elif any(kw in query for kw in cancel_keywords):
        intent = "cancel"
    elif any(kw in query for kw in ["什麼", "有哪些", "啥", "推薦"]):
        intent = "query"
    else:
        intent = "order"

    # 提取客製化
    for kw in customize_keywords:
        if kw in query:
            customizations.append(kw)

    # 提取尺寸
    size = None
    for sz in size_keywords:
        if sz in query:
            size = sz
            break

    # 解析點餐或取消
    if intent in ["order", "cancel"]:
        for doc in docs:
            content = doc.page_content.lower()
            item_name = doc.metadata["name"].lower()
            if item_name in query:
                price_match = re.search(r"價格:\s*([\d\s]+)", content)
                price = int(price_match.group(1).replace(" ", "")) if price_match else 0

                if doc.metadata["table"] == "combos":
                    main_match = re.search(r"主餐:\s*([^\n]+)", content)
                    side_match = re.search(r"配餐:\s*([^\n]+)", content)
                    drink_match = re.search(r"飲料:\s*([^\n]+)", content)
                    components = {
                        "main": main_match.group(1) if main_match else "未知",
                        "side": side_match.group(1) if side_match else "未知",
                        "drink": drink_match.group(1) if drink_match else "未知"
                    }
                    item_info = {
                        "name": doc.metadata["name"],
                        "price": price,
                        "type": "套餐",
                        "components": components,
                        "customizations": customizations
                    }
                else:
                    item_info = {
                        "name": doc.metadata["name"],
                        "price": price,
                        "type": doc.metadata["table"],
                        "customizations": customizations
                    }
                if size and doc.metadata["table"] in ["side_orders", "drinks"]:
                    size_price_match = re.search(rf"{size}\)\s*(\d+)", content)
                    if size_price_match:
                        item_info["price"] = int(size_price_match.group(1))
                        item_info["customizations"].append(f"尺寸:{size}")
                break

    # 更新訂單狀態
    if intent == "order" and item_info:
        order_state["items"].append(item_info)
        order_state["total_price"] += item_info["price"]
    elif intent == "cancel" and item_info:
        for item in order_state["items"][:]:
            if item["name"].lower() == item_info["name"].lower():
                order_state["items"].remove(item)
                order_state["total_price"] -= item["price"]
    elif intent == "confirm" and order_state["items"]:
        order_state["status"] = "confirm"
    elif intent == "end":
        order_state["status"] = "end"

    return intent, order_state

# RAG 檢索 + 生成回應
def rag_query(query, vectorstore, order_state):
    # 檢索相關菜單
    try:
        docs = vectorstore.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"RAG 檢索失敗：{e}")
        context = "暫無菜單資訊"

    # 解析用戶意圖和訂單
    intent, order_state = parse_user_input(query, docs, order_state)

    # 準備 LLM 上下文
    system_prompt = '''
    你是一個麥當勞點餐店員，負責幫顧客快速點餐、確認訂單、回答菜單問題，態度要親切、熱情，像在台灣麥當勞櫃檯服務一樣！用台灣口語，回應要自然、簡潔，帶點溫暖的語氣。你的任務是根據提供的菜單資訊、用戶查詢和訂單狀態，生成符合點餐場景的回應。

    **指令**：
    1. **根據菜單資訊**：用提供的菜單內容（包含品項、價格、類別、描述、客製選項、套餐細節）來回答，確保資訊準確。
    2. **根據意圖回應**：
    - 如果意圖是「order」（點餐），確認新增的品項並問是否繼續點餐（例如「好的，大麥克 89 元！要不要加點飲料或甜點？」）。
    - 如果意圖是「cancel」（取消），確認移除的品項並問還有什麼需求（例如「好的，大麥克已取消！還要啥？」）。
    - 如果意圖是「query」（查詢），列出相關品項或回答問題，語氣熱情（例如「我們有大麥克 89 元、麥香雞 55 元，你想試哪個？」）。
    - 如果意圖是 [know] (知道)，列出用戶所點的品項和價格（例如「你目前的訂單有：大麥克 89 元，薯條無鹽 45 元，總共 134 元」）。
    - 如果意圖是「confirm」（確認），列出訂單總覽（品項、客製、總價）並問「內用還是外帶？」（例如「訂單：大麥克 89 元，薯條無鹽 45 元，總共 134 元。內用還是外帶？」）。
    - 如果意圖是「end」（結束），若有訂單，確認訂單並結束（例如「訂單確認，謝謝光臨！」）；若無訂單，說「好的，謝謝光臨！」。
    - 如果意圖是「unknown」（聽不懂），說「可以再說一次嗎？我幫你弄清楚！」。
    3. **錯誤處理**：
    - 如果菜單資訊不足或查詢不在菜單（像「披薩」），回應「不好意思，我們目前沒有這個品項哦！要不要試試大麥克或麥香雞？」。
    4. **回應風格**：
    - 用台灣口語，像「好的！」「沒問題！」「馬上幫你弄！」。
    - 語氣親切，像在跟朋友聊天，但保持專業。
    - 回應簡潔，重點突出（價格、品項、選項），避免太長。
    - 適時加點溫暖語氣，例如「馬上幫你準備好哦！」或「這樣可以吧？」。

    **菜單資訊格式**：
    - 單點：品項、類別、價格、描述（例如「品項: 大麥克\n類別: 牛肉\n價格: 89 元\n描述: 雙層純牛肉，獨特大麥克醬...」）。
    - 配餐：配餐名、價格、尺寸選項（例如「配餐: 薯條\n價格: 45 (中) / 60 (大)\n尺寸選項: 中,大,(小)」）。
    - 套餐：套餐名、主餐、配餐、飲料、價格（例如「套餐: 大麥克經典套餐\n主餐: 大麥克\n配餐: 薯條\n飲料: 可口可樂®\n價格: 159 元」）。

    **訂單狀態**（JSON 格式）：
    {
        "items": [
            {"name": "大麥克", "price": 89, "type": "單點", "customizations": []},
            {"name": "薯條", "price": 45, "type": "配餐", "customizations": ["無鹽"]}
        ],
        "total_price": 134,
        "status": "ongoing"  # 或 "confirm", "end"
    }

    **範例**：
    - 意圖：order，訂單新增大麥克
    回應：好的，大麥克 89 元！要不要配中薯和可樂變經典套餐，159 元超划算？
    - 意圖：cancel，移除大麥克
    回應：好的，大麥克已取消！還要點什麼？
    - 意圖：query，用戶問「有什麼飲料？」
    回應：我們有可口可樂、雪碧、檸檬茶、無糖綠茶，價格 35 到 80 元。你想喝啥？
    - 意圖：confirm
    回應：訂單：大麥克 89 元，薯條無鹽 45 元，總共 134 元。內用還是外帶？
    - 意圖：end
    回應：好的，謝謝光臨！

    開始吧！根據用戶查詢、菜單資訊、訂單狀態和意圖，生成親切的回應！
    '''
    prompt = f"{system_prompt}\n\n菜單資訊:\n{context}\n\n當前訂單狀態:\n{json.dumps(order_state, ensure_ascii=False, indent=2)}\n\n用戶意圖: {intent}\n\n用戶: {query}\n助手: "

    # 用 Ollama 生成回應
    try:
        response = ollama.generate(model="gemma3:1b", prompt=prompt, options={
            "temperature": 0.8,
            "top_k": 40,
            "top_p": 0.95,
            "num_ctx": 2048,
            "chat_template_kwargs": {"enable_thinking": True}
        })['response']
        # 清 GPU 記憶體
        torch.cuda.empty_cache()
        return response, order_state
    except Exception as e:
        print(f"Ollama 推理失敗：{e}")
        return "不好意思，系統出了點問題，可以再說一次你的需求嗎？", order_state

# 互動式點餐對話
def interactive_ordering():
    vectorstore = load_menu_to_vectorstore()
    order_state = {
        "items": [],
        "total_price": 0,
        "status": "ongoing"
    }
    print("歡迎來到麥當勞！請問要點什麼？（輸入 '結束' 或 '確認' 完成訂單）")

    while order_state["status"] == "ongoing":
        query = input("> ")
        response, order_state = rag_query(query, vectorstore, order_state)
        print(response)
        if order_state["status"] in ["confirm", "end"]:
            if order_state["items"] and order_state["status"] == "confirm":
                # 確認後繼續問內用/外帶
                query = input("> ")
                response, order_state = rag_query(query, vectorstore, order_state)
                print(response)
                order_state["status"] = "end"
            break

if __name__ == "__main__":
    interactive_ordering()