# File: rag_retrieval.py
# 晨間廚房語音點餐系統，基於 morning_eat.xlsx，LLM 回傳 id 給系統，顧客用自然語言，生成 JSON 訂單並匯出
import json
import ollama
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import torch
import re
from CRUD_database import create_connection, query_main_menu, query_combo_menu, query_name_to_price

# 初始化嵌入模型
try:
    embedding_model = OllamaEmbeddings(model="qwen3:0.6b")
except Exception as e:
    print(f"嵌入模型載入失敗：{e}")
    raise e

# 從 Chroma 載入向量資料庫
def load_menu_to_vectorstore(persist_directory: str = "./chroma_db", name: str = "morning_menu"):
    try:
        vectorstore = Chroma(
            collection_name=name,
            embedding_function=embedding_model,
            persist_directory=persist_directory
        )
        print("向量資料庫載入成功")
        return vectorstore
    except Exception as e:
        print(f"Chroma 資料庫載入失敗：{e}")
        print("請確認 ./chroma_db 存在，或重新跑 load_menu_to_chroma.py 生成資料庫")
        raise e

# 初始化訂單
def init_order_state():
    return {
        "items": [],
        "total_price": 0,
        "status": "ongoing"
    }

# RAG 檢索 + LLM 生成回應 + 解析訂單
def rag_query(query, vectorstore, order_state, cus_choice):
    # 檢索相關菜單
    try:
        docs = vectorstore.similarity_search(query, k=10)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"RAG 檢索失敗：{e}")
        context = "暫無菜單資訊"
    # print(context)

    prompt, ex_json = create_prompt_template()

    # 用 Ollama 生成回應
    try:
        model = OllamaLLM(model="qwen3:0.6b", temperature=0.7, top_k=30, top_p=0.9, max_tokens=2048)

        chain = prompt | model

        response = chain.invoke({'json': ex_json, 'context': context, 'order_state': order_state, 'query': query})

        print(f"LLM 回應：{response}")
        exit()

        # 解析 LLM 回應，更新訂單
        customer_response, new_order_state = parse_llm_response(response.content, order_state, cus_choice)
        return customer_response, new_order_state
    except Exception as e:
        print(f"Ollama 推理失敗：{e}")
        return "不好意思，系統出了點問題，可以再說一次你的需求嗎？", order_state

def query_db(item_id):
    conn = create_connection()
    if item_id.isnumeric():
        result = query_main_menu(conn, item_id)
    else:
        result = query_combo_menu(conn, item_id)
    conn.close()
    return result

def query_price(cls: str, name: str):
    conn = create_connection()
    result = query_name_to_price(conn, cls, name)
    conn.close()
    return result

def change_order(order_state, status, item, quantity, customizations, cus_price = 0):
    if status == "+":
        order_state["total_price"] += item['price'] * quantity
        for existing_item in order_state["items"]:
            if existing_item['id'] == item['id']:
                existing_item['quantity'] += quantity
                if customizations != "無":
                    existing_item['cus_price'].append(cus_price)  
                    existing_item['customizations'].append(customizations)
                return 
        order_state["items"].append({
            "id": item['id'],
            "class": item['class'],
            "name": item['name'],
            "price": item['price'],
            "quantity": quantity,
            "cus_price": cus_price,
            "customizations": [customizations]
        })
    elif status == "-":
        for existing_item in order_state["items"]:
            if existing_item['id'] == item['id']:
                quantity_diff = min(quantity, existing_item['quantity'])
                existing_item['quantity'] -= quantity_diff
                existing_item['total_price'] -= item['price'] * quantity_diff
                existing_item['total_price'] -= item['cus_price'] * quantity_diff
            if existing_item['quantity'] <= 0:
                order_state["items"].remove(existing_item)
                return

def deal_with_cus(cus, cus_choice):
    cus_price = 0
    for key, value in cus_choice.items():
        if key in cus:
            cus_price += value
    return cus, cus_price
def parse_llm_response(response, order_state, cus_choice):
    # 找到sys和cus的區塊
    sys_block = re.search(r"```sys\n(.*?)```", response, re.DOTALL)
    cus_block = re.search(r"```cus\n(.*?)```", response, re.DOTALL)
    if sys_block:
        sys_content = sys_block.group(1).strip()
    else:
        sys_content = ""
    if cus_block:
        cus_content = cus_block.group(1).strip()
    else:
        cus_content = ""
    # 解析系統回應
    sys_lines = sys_content.split("\n")
    for line in sys_lines:
        if line.startswith("intent:"):
            intent = line.split(":")[1].strip()
            order_state["status"] = intent
        if line.startswith("+"):
            action, item_id, quantity, cus = line.split()
            result = query_db(item_id)
            cus_price = deal_with_cus(cus, cus_choice)
            change_order(order_state, action, result, int(quantity), cus, cus_price)
        if line.startswith("-"):
            action, item_id, quantity = line.split()
            change_order(order_state, action, result, int(quantity), cus)
    new_cus_content = ""
    for line in cus_content.split("\n"):
        new_line = ""
        prev = ""
        for word in line.split():
            prev = word
            if word == "$$$":
                cls, name = prev.split("-")
                item = query_price(cls, name)
                word = item['price']
            new_line += word + " "
        new_cus_content.append
    return cus_content, order_state
            
def create_prompt_template():
    example_json = {
          "items": [
              {
                  "id": 1,
                  "class": "台式蛋餅",
                  "name": "原味",
                  "price": 30,
                  "quantity": 1,
                  "cus_price": [35],
                  "customizations": ["雙蛋、起司、泡菜"]
              },
            ],
            "total_price": 65,
          "status": "ongoing"
      }
    template = '''
      你是一個晨間廚房早餐店店員，負責幫顧客快速點餐、確認訂單、回答菜單問題，態度要親切、熱情，像在台灣早餐店櫃檯服務一樣！你的任務是根據顧客的自然語言查詢、菜單資訊和當前訂單狀態，生成兩部分純文字回應：
      1. **給系統**：這輪顧客點了什麼或刪除了什麼品項的 id 編號及數量以及客製化內容。
      2. **給顧客**：親切的台灣口語回應，包含"完整"品項名稱、價格(請用$$$標示)、客製等。

      **指令**：

      ### 1. 給系統（id 編號及數量）
      - 從顧客查詢和菜單資訊提取品項，輸出 id 編號及數量。
      - **格式**：
        - <id> 請依照"菜單資訊"上面提供的 id 照實填寫
        - <數量> 請依照顧客查詢的數量填寫，若查詢未明確數量，假設 1 份
        - <客製化> 請依照顧客查詢的客製化由你判斷填寫，若有出現在"菜單資訊"上請依照菜單資訊上填寫，若查詢未明確客製化，則填寫「無」。
        - 新增：`+ <id> <數量> <客製化>`（例如「+ 1 1 無」表示 id 1 品項 1 份）。
        - 取消：`- <id> <數量>`（例如「- 1 1」表示取消 id 1 品項 1 份）。
        - 每行一個動作，無動作時留空。
      - **意圖**：
        - **點餐 (order)**：提取品項 id 和數量（「我要一份蛋餅」→ 「+ 1 1 無」）。
        - **取消 (cancel)**：識別取消品項（「蛋餅不要了」→ 「- 1 1」）。
        - **查詢菜單 (query)**：不輸出 id（例如「有什麼飲料？」不生成系統回應）。
        - **確認訂單 (view_cus)**：不輸出 id，僅生成顧客回應。
        - **結束對話 (end)**：不輸出 id，僅生成顧客回應。
        - **找不到品項 (unknown)**：若查詢無匹配 id，輸出「系統：無對應品項」。
      - **數量處理**：
        - 若查詢未明確數量（例如「我要蛋餅」），假設 1 份。
        - 若查詢含數量（例如「兩份蛋餅」），使用指定數量。

      ### 2. 給顧客（親切回應）
      - 依照"菜單資訊"做回答，請勿隨意編造品項或價格。
      - **點餐**：依照"菜單資訊"列出類別-品項名稱、價格、客製，詢問是否繼續點餐或客製（例如「好的，台式蛋餅-原味 $$$ 元！要不要加起司或泡菜或套餐？」）。
      - **套餐**：列出套餐名稱、價格、內容物（例如「原味蛋餅 A套餐 65 元，含薯餅和中杯紅茶！」）。
      - **客製**：列出客製選項（例如「玉米蛋餅加起司加泡菜加雙蛋 40 元！」）。
      - **取消**：確認移除品項（例如「好的，蛋餅已取消！還要啥？」）。
      - **查詢菜單**：列出相關品項名稱和價格（例如「我們有古早紅茶 20 元、英式奶茶 25 元，你想喝啥？」）。
      - **確認訂單**：列出訂單總覽（品項、客製、價格、總價），並問「內用還是外帶？」（例如「訂單：原味蛋餅 30 元，紅茶大杯 25 元，總共 55 元。內用還是外帶？」）。
      - **結束對話**：
        - 若有訂單：確認訂單並結束（例如「訂單確認，謝謝光臨！」）。
        - 若無訂單：說「好喔，謝謝光臨！」。
      - **找不到品項**：回應「不好意思，沒這品項，可以再說清楚嗎？」。
      - **回應風格**：
        - 用台灣口語，例如「好喔！」「沒問題！」「馬上幫你弄！」。
        - 語氣親切，像跟朋友聊天，但保持專業。
        - 回應簡潔，重點突出（品項、價格、客製），適時加溫暖語氣（例如「這樣可以吧？」）。

      ### 處理細節
      - **模糊輸入**：
        - 若查詢模糊（例如「蛋餅」），選 id 對應「原味蛋餅」（id 1）。
        - 若查詢含多品項（例如「青花椒堡，跟大冰紅」），逐一提取 id 和數量。
      - **客製**：
        - 識別客製選項：雙蛋、起司、泡菜、無糖、去冰、少冰、加糖、中杯、大杯。
        - 若提到「大冰紅」，選 id 112（古早紅茶大杯，價格 25 元）。
        - 客製記錄在顧客回應中（例如「紅茶無糖 20 元」）。
      - **套餐**：
        - 若提到「A」「B」「C」「D」，選對應套餐 id（例如 id A1 為「原味蛋餅 A套餐」，價格 = 主餐價格 + 35 元）。
        - 套餐價格：A（35 元）、B/C/D（50 元）。
        - 回應包含套餐內容（例如「原味蛋餅 A套餐 65 元，含薯餅和中杯紅茶」）。
      - **錯誤處理**：
        - 若查詢不在菜單（例如「披薩」），輸出「系統：無對應品項」和「不好意思，沒這品項，可以再說清楚嗎？」。
        - 若查詢不明確（例如「早餐」），回應「可以再說清楚點嗎？我幫你弄清楚！」。
      - **訂單查詢**：
        - 若查詢含「確認」「看看訂單」，根據訂單狀態列出品項、客製、價格和總價。

      ### 菜單資訊格式
      - **單點**：
        - 欄位：id、品項、類別、價格(元)、雙蛋(0=不可選|1=可選)、起司(0=不可選|1=可選)、泡菜(0=不可選|1=可選)、山形丹麥(0=不可選|1=可選)、套餐(A/B/C/D=可選套餐|0=不可選)、素食(0=不可食|1=可食)、推薦(0=普通|1=推薦)。
        - 範例：
          ```
          id: 1
          品項: 原味蛋餅
          類別: 台式蛋餅
          價格: 30
          起司: 1
          泡菜: 1
          套餐: A/B/C/D
          素食: 1
          ```
          ```
          id: 1001
          品項: 古早紅茶
          類別: 特調飲品
          價格: 25
          素食: 1
          推薦: 1
          ```
      - **套餐**：
        - 欄位：id、套餐名、價格、內容物。
        - 範例：
          ```
          id: A1
          套餐: 原味蛋餅 A套餐
          價格: 65
          內容物: 原味蛋餅+薯餅+中杯古早紅茶
          ```
          ```
          id: B1
          套餐: 原味蛋餅 B套餐
          價格: 80
          內容物: 原味蛋餅+薯條+中杯古早紅茶
          ```

      ### 當前訂單狀態（JSON 格式）
      {json}
      

      ### 輸出格式（純文字）
      ```
      ```sys
      intent: order
      + 1 1 無
      ```
      ```cus
      好的，台式蛋餅-原味 $$$ 元！要不要加套餐？
      ```
      ```
      或
      ```
      ```sys
      intent: unknown
      系統：無對應品項
      ```
      ```cus
      不好意思，沒這品項，可以再說清楚嗎？
      ```
      ```

      ### 範例
      1. **查詢**：我要一份蛋餅
        ```
        ```sys
        intent: order
        + 1 1 無
        ```
        ```cus
        好的，台式蛋餅-原味 $$$ 元！要不要加起司或泡菜？
        ```
        ```
      2. **查詢**：我要一份玉米蛋餅加起司加泡菜加雙蛋
        ```
        ```sys
        intent: order
        + 1 1 雙蛋、起司、泡菜
        ```
        ```cus
        好的，台式蛋餅-玉米 加起司加泡菜加雙蛋 $$$ 元！要不要套餐？
        ```
        ```

      3. **查詢**：青花椒堡，跟大冰紅
        ```
        ```sys
        intent: order
        + 40 1 無
        + 112 1 無
        ```
        ```cus
        好喔，漢堡-青花椒豬堡 55 元，特調飲品-古早紅茶-L 30 元！還要啥？
        ```
        ```

      4. **查詢**：蛋餅不要了
        ```
        ```sys
        intent: cancel
        - 1 1
        ```
        ```cus
        好的，台式蛋餅-原味已取消！還要啥？
        ```
        ```

      5. **查詢**：有什麼飲料？
        ```
        ```sys
        intetnt: query
        ```
        ```cus
        我們有古早紅茶-M 20 元、英式奶茶 25 元、鮮奶咖啡 40 元，你想喝啥？
        ```
        ```

      5. **查詢**：確認一下我的餐點
        ```
        ```sys
        intent: view_cus
        ```
        ```cus
        訂單：原味蛋餅 30 元，紅茶大杯 25 元，總共 55 元。內用還是外帶？
        ```
        ```

      6. **查詢**：披薩
        ```
        ```sys
        intent: unknown
        系統：無對應品項
        ```
        ```cus
        不好意思，沒這品項，可以再說清楚嗎？
        ```
        ```

      7. **查詢**：蛋餅 A套餐
        ```
        ```sys
        intent: order
        + 1 1 無
        + A1 1
        ```
        ```cus
        好的，原味蛋餅 A套餐 65 元，含薯餅和中杯紅茶！還要啥？
        ```
        ```

      8. **查詢**：結束
        ```
        ```sys
        intent: end
        ```
        ```cus
        好喔，謝謝光臨！
        ```
        ```

      開始吧！根據顧客查詢、菜單資訊和訂單狀態，生成給系統的 id 編號及數量，以及給顧客的親切回應！
      菜單資訊:
        {context}
      當前訂單狀態:
        {order_state}
      用戶:
        {query}
      助手:

      '''
    prompt = PromptTemplate(
        template=template,
        input_variables=["json", "context", "order_state", "query"]
    )
    return prompt, example_json

# 互動式點餐對話
def interactive_ordering():
    cus_choice = {"雙蛋": 15, "起司": 10, "泡菜": 10, '燒肉': 20, '起司牛奶': 5, '山型丹麥': 10}
    vectorstore = load_menu_to_vectorstore(name="morning_menu")
    test = vectorstore.similarity_search("我要一份蛋餅", k=10)
    print(f"檢索到 {len(test)} 筆相關菜單")
    order_state = init_order_state()
    print("歡迎來到晨間廚房！請問要點什麼？（輸入 '結束' 或 '確認' 完成訂單）")

    while order_state["status"] != "end":
        query = input("> ")
        response, order_state = rag_query(query, vectorstore, order_state, cus_choice)
        print(response)
        if order_state["status"] == "end":
            break

    # 匯出最終訂單 JSON
    print("\n最終訂單：")
    print(json.dumps(order_state, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    interactive_ordering()