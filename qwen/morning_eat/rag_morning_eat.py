# File: rag_retrieval.py
# 晨間廚房語音點餐系統，基於 morning_eat.xlsx，LLM 回傳 id 給系統，顧客用自然語言，生成 JSON 訂單並匯出
import json
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from CRUD_database import create_connection, query_drink_menu, query_main_menu, query_combo_menu, query_name_to_price
from useModel import useModel
import re

# 初始化嵌入模型
try:
    embedding_model = OllamaEmbeddings(model="deepseek-r1:1.5b")
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
        docs = vectorstore.similarity_search(query, k=50)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"RAG 檢索失敗：{e}")
        context = "暫無菜單資訊"
    # print(context)

    prompt, ex_json = create_prompt_template()

    # 用 Ollama 生成回應
    try:
        model = useModel("gemini_api")

        chain = prompt | model

        response = chain.invoke({'json': ex_json, 'context': context, 'order_state': order_state, 'query': query})

        if response.content != None:
            response = response.content
        #     print("Ollama 回應：", response)
        print(response)
        # exit()
#         response = '''
# ```sys
# intent: order
# + 19 1 加蛋
# + 1001 1 大杯
# ```
# ```cus
# 好喔，吐司-奶油加蛋 30 元，特調飲品-古早紅茶大杯 30 元！這樣總共 60 元，還要點些什麼嗎？
# ```
#         '''
        # print(response)

        # 解析 LLM 回應，更新訂單
        customer_response, new_order_state = parse_llm_response(response, order_state, cus_choice)
        return customer_response, new_order_state
    except Exception as e:
        print(f"Ollama 推理失敗：{e}")
        return "不好意思，系統出了點問題，可以再說一次你的需求嗎？", order_state

def query_db(item_id):
    conn = create_connection()
    if item_id.isnumeric() and int(item_id) > 1000:
        print("查詢飲品菜單")
        result = query_drink_menu(conn, item_id)
    elif item_id.isnumeric():
        print("查詢主餐菜單")
        result = query_main_menu(conn, item_id)
    else:
        print("查詢套餐菜單")
        result = query_combo_menu(conn, item_id)
    conn.close()
    return result

def query_price(cls: str, name: str):
    conn = create_connection()
    result = query_name_to_price(conn, cls, name)
    conn.close()
    return result

def gen_random_id():
    import random
    return str(random.randint(1000, 9999))

def deal_with_price(item, cus):
    if item.get('price', None) is not None:
        return item['price']
    if cus == "大杯":
        return item['L']
    return item['M']


def change_order(order_state, status, item, quantity, customizations = "", cus_price = 0):
    print("餐點解析中")
    if status == "+":
        item_price = deal_with_price(item, customizations)
        print("新增餐點")
        for existing_item in order_state["items"]:
            if existing_item['item_id'] == item['id'] and existing_item['customization']['note'] == customizations:
                existing_item['quantity'] += quantity
                order_state['total_price'] += existing_item['subtotal'] * quantity
                return order_state
        print("新增餐點二")
        order_state["items"].append({
            "id": str(item.get('id', "未知")) + gen_random_id(),
            "item_id": item.get('id', "未知"),
            "class": item.get('class', '套餐'),
            "name": item.get('name', '未知'),
            "unitPrice": item_price,
            "subtotal": item_price + cus_price,
            "quantity": quantity,
            "customization": {
                "cus_price": cus_price,
                "note": customizations,
            }
        })
        order_state['total_price'] += (item_price + cus_price) * quantity
        return order_state
    elif status == "-":
        for existing_item in order_state["items"]:
            if existing_item['id'] == item:
                quantity_diff = min(quantity, existing_item['quantity'])
                existing_item['quantity'] -= quantity_diff
                order_state['total_price'] -= existing_item['subtotal'] * quantity_diff
            if existing_item['quantity'] <= 0:
                order_state["items"].remove(existing_item)
                return order_state
    return order_state

def deal_with_cus(cus, cus_choice):
    cus_price = 0
    for key, value in cus_choice.items():
        if key in cus:
            cus_price += value
    return cus, cus_price
def parse_llm_response(response, order_state, cus_choice):
    print(order_state)
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
    print("Start parsing sys block")
    for line in sys_lines:
        if line.startswith("intent:"):
            intent = line.split(": ")[1].strip()
            order_state["status"] = intent
        if line.startswith("+"):
            action, item_id, quantity, cus = line.split()
            result = query_db(item_id)
            cus, cus_price = deal_with_cus(cus, cus_choice)
            order_state = change_order(order_state, action, result, int(quantity), cus, cus_price)
        if line.startswith("-"):
            action, item_id, quantity = line.split()
            order_state = change_order(order_state, action, item_id, int(quantity))
    print("End parsing sys block")
    # new_cus_content = ""
    # for line in cus_content.split("\n"):
    #     new_line = ""
    #     prev = ""
    #     for word in line.split():
    #         prev = word
    #         if word == "$$$":
    #             cls, name = prev.split("-")
    #             item = query_price(cls, name)
    #             word = item['price']
    #         new_line += word + " "
    #     new_cus_content.append
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
    1. **給系統**：這輪顧客點了什麼或刪除了什麼品項的 id 編號及數量，以及客製化內容。
    2. **給顧客**：親切的台灣口語回應，包含完整品項名稱、價格（用 OO 元標示）、客製等。

    ---

    ### 指令

    #### 1. 給系統（id 編號及數量）
    - 從顧客查詢和菜單資訊提取品項，輸出 id 編號及數量。
    - **格式**：
      - **新增**：`+ <id> <數量> <客製化>`（例如 `+ 1 1 無` 表示 id 1 品項 1 份，無客製）。
      - **取消**：`- <訂單id> <數量>`（例如 `- 12313 1` 表示取消訂單中 id 1 品項 1 份）。
      - **每行一個動作**，無動作時留空。
      - **客製化**：列出所有客製選項（例如 `雙蛋、起司、泡菜`），若無客製則填 `無`。僅記錄菜單資訊中可用的客製選項（例如雙蛋、起司、泡菜、無糖、去冰、少冰、加糖、中杯、大杯）。
    - **意圖**：
      - **點餐 (order)**：提取品項 id 和數量（例如「我要一份蛋餅」→ `+ 1 1 無`）。
      - **取消 (cancel)**：識別取消品項（例如「蛋餅不要了」→ `- 12323 1`）。
      - **查詢菜單 (query)**：不輸出 id（例如「有什麼飲料？」）。
      - **確認訂單 (view_cus)**：不輸出 id，僅生成顧客回應。
      - **結束對話 (end)**：不輸出 id，僅生成顧客回應、不要輸出訂單。
      - **找不到品項 (unknown)**：輸出 `系統：無對應品項`。
    - **數量處理**：
      - 未明確數量（例如「我要蛋餅」），假設 1 份。
      - 明確數量（例如「兩份蛋餅」），使用指定數量。
    - **模糊輸入**：
      - 若查詢模糊（例如「蛋餅」），選「原味蛋餅」（id 1）。
      - 若查詢多品項（例如「青花椒堡，大冰紅」），逐一提取 id 和數量。
    - **套餐**：
      - 若提到「A」「B」「C」「D」，選對應套餐 id（例如 id A1 為「A套餐」）。
      - 若點主餐+套餐（例如「蛋餅 A套餐」），記錄主餐 id 和套餐 id。

    #### 2. 給顧客（親切回應）
    - 依照菜單資訊回答，**不得編造品項或價格**。
    - **點餐**：
      - 列出**類別-品項名稱**、價格（用 OO 元 標示）、客製。
      - 詢問是否繼續點餐或客製（例如「好喔，台式蛋餅-原味 30 元！要加起司、泡菜，還是套餐？」）。
      - 若點套餐，列出套餐內容（例如「原味蛋餅 A套餐 65 元，含晨間薯餅和中杯古早紅茶！」）。
    - **取消**：
      - 確認移除品項（例如「好啦，台式蛋餅-原味取消囉！還要啥？」）。
    - **查詢菜單**：
      - 列出相關品項和價格，簡潔且熱情（例如「飲料有古早紅茶 20 元、鮮奶茶 25 元，想喝啥？」）。
      - 若查詢廣泛（例如「有啥好吃的？」），推薦 2-3 個「推薦」品項（菜單中有「推薦: 1」）。
    - **確認訂單**：
      - 列出訂單總覽（品項、客製、價格、總價），問「內用還是外帶？」（例如「訂單：原味蛋餅 30 元，古早紅茶-L 30 元，總共 60 元。內用還是外帶？」）。
      - 若無訂單，說「目前沒點餐喔，要不要來點啥？」。
    - **結束對話**：
      - 有訂單：確認訂單並結束（例如「訂單確認！馬上幫你弄，謝謝光臨！」）。
      - 無訂單：說「好喔，謝謝光臨，歡迎再來！」。
    - **找不到品項**：
      - 回應「哎呀，沒這品項耶！可以再說清楚一點嗎？」。
    - **回應風格**：
      - 用**台灣早餐店口語**，例如「好喔！」「馬上好！」「這樣可以吧？」「來啦！」。
      - 語氣像跟熟客聊天，親切但專業（例如「好啦，馬上幫你弄好！」）。
      - 簡潔突出重點（品項、價格、客製），適時加溫暖語氣（例如「好吃又划算喔！」）。
    - **客製**：
      - 確認客製選項（例如「玉米蛋餅加起司加泡菜 40 元！」）。
      - 若提到「大冰紅」，選古早紅茶大杯（id 1001，L大杯 30 元）。
    - **推薦**：
      - 若顧客猶豫（例如「有啥好吃的？」），優先推薦「推薦: 1」的品項。
    - **錯誤處理**：
      - 查詢不明確（例如「早餐」）：回應「嘿，可以說得清楚點嗎？像蛋餅、吐司還是啥？」。
      - 重複點餐：提示「這品項已經點過囉，要再加一份嗎？」。

    #### 處理細節
    - **套餐價格**：
      - A套餐：主餐價格 + 35 元（含晨間薯餅+中杯古早紅茶）。
      - B/C/D套餐：主餐價格 + 50 元（B: 薯條+紅茶；C: 麥克雞塊+紅茶；D: 生菜沙拉+紅茶）。
    - **飲料客製**：
      - 預設中杯，若指定「大杯」或「大冰紅」，選大杯價格。
      - 無糖、去冰、少冰、加糖等客製記錄在回應中（例如「古早紅茶無糖 20 元」）。
    - **訂單狀態**：
      - 若訂單已有品項，確認訂單時顯示所有品項、客製、價格和總價。
      - 若顧客取消不存在的品項，回應「這品項沒在訂單裡喔！要點啥新的嗎？」。
    - **文化細節**：
      - 早餐店常快速確認訂單，語氣輕鬆（例如「好啦，這樣對吧？」）。
      - 常推銷套餐或熱門品項（例如「要不要加個 A套餐？超划算！」）。
      - 若顧客問「有啥快一點的？」，優先推薦簡單品項（例如吐司、蛋餅）。

    #### 菜單資訊格式
    - **單點**：
      - 欄位：id、類別、品項名稱、價格、雙蛋(0=不可選|1=可選)、起司(0=不可選|1=可選)、泡菜(0=不可選|1=可選)、燒肉(0=不可選|1=可選)、起司牛奶(0=不可選|1=可選)、山型丹麥(0=不可選|1=可選)、套餐(A/B/C/D=可選|無=不可選)、素食(0=不可食|1=可食)、推薦(0=普通|1=推薦)。
      - 範例：
        ```
        id: 1
        類別: 台式蛋餅
        品項名稱: 原味
        價格: 30.0 元
        起司: 1
        泡菜: 1
        套餐: A/B/C/D
        素食: 1
        ```
    - **套餐**：
      - 欄位：id、套餐名稱、價格、內容物。
      - 範例：
        ```
        id: A1
        套餐名稱: A
        價格: 35.0 元
        內容物: 晨間薯餅+中杯紅茶(古早)
        ```
    - **飲料**：
      - 欄位：id、飲品名稱、中杯價格、大杯價格。
      - 範例：
        ```
        id: 1001
        飲品名稱: 古早紅茶
        M中杯: 20.0 元
        L大杯: 30.0 元
        ```

    #### 輸出格式（純文字）
    ```
    ```sys
    intent: <intent>
    + <id> <數量> <客製化>
    - <訂單id> <數量>
    ```
    ```cus
    好喔，台式蛋餅-原味 30 元！要加套餐或啥客製嗎？
    ```
    ```
    或
    ```
    ```sys
    intent: unknown
    系統：無對應品項
    ```
    ```cus
    哎呀，沒這品項耶！可以再說清楚一點嗎？
    ```
    ```

    #### 範例
    1. **查詢**：我要一份蛋餅
      ```
      ```sys
      intent: order
      + 1 1 無
      ```
      ```cus
      好喔，台式蛋餅-原味 30 元！要加起司、泡菜，還是套餐？
      ```
      ```

    2. **查詢**：玉米蛋餅加起司加泡菜加雙蛋
      ```
      ```sys
      intent: order
      + 2 1 雙蛋、起司、泡菜
      ```
      ```cus
      好啦，台式蛋餅-玉米 加起司、泡菜、雙蛋 40 元！要不要加個套餐？
      ```
      ```

    3. **查詢**：青花椒堡，大冰紅
      ```
      ```sys
      intent: order
      + 40 1 無
      + 1001 1 大杯
      ```
      ```cus
      來啦，漢堡-青花椒豬堡 55 元，特調飲品-古早紅茶大杯 30 元！還要啥好吃的？
      ```
      ```

    4. **查詢**：蛋餅不要了
      ```
      ```sys
      intent: cancel
      - 12313 1
      ```
      ```cus
      好啦，台式蛋餅-原味取消囉！還想吃啥？
      ```
      ```

    5. **查詢**：有什麼飲料？
      ```
      ```sys
      intent: query
      ```
      ```cus
      飲料有古早紅茶 20 元、英式奶茶 25 元、鮮奶咖啡 40 元，推薦古早紅茶，清爽好喝！想喝啥？
      ```
      ```

    6. **查詢**：確認一下我的餐點
      ```
      ```sys
      intent: view_cus
      ```
      ```cus
      訂單：台式蛋餅-原味 30 元，特調飲品-古早紅茶大杯 30 元，總共 60 元。內用還是外帶？
      ```
      ```

    7. **查詢**：披薩
      ```
      ```sys
      intent: unknown
      系統：無對應品項
      ```
      ```cus
      哎呀，沒披薩這品項耶！要不要試試我們的台式蛋餅或吐司？
      ```
      ```

    8. **查詢**：蛋餅 A套餐
      ```
      ```sys
      intent: order
      + 1 1 無
      + A1 1 無
      ```
      ```cus
      好喔，台式蛋餅-原味 A套餐 65 元，含晨間薯餅和中杯古早紅茶！還要加啥？
      ```
      ```

    9. **查詢**：有啥好吃的？
      ```
      ```sys
      intent: query
      ```
      ```cus
      推薦我們的台式蛋餅-鮪魚玉米 45 元、吐司-巧克力 20 元，還有漢堡-美式牛肉堡 65 元，超夯！想吃哪個？
      ```
      ```

    10. **查詢**：結束
      ```
      ```sys
      intent: end
      ```
      ```cus
      好啦，訂單確認！馬上幫你弄好，謝謝光臨！
      ```
      ```

    ---

    ### 當前訂單狀態（JSON 格式）
    {json}

    ### 開始吧！
    根據顧客查詢、菜單資訊和訂單狀態，生成給系統的 id 編號及數量，以及給顧客的親切回應！
    - **菜單資訊**: {context}
    - **當前訂單狀態**: {order_state}
    - **用戶查詢**: {query}

      '''
    prompt = PromptTemplate(
        template=template,
        input_variables=["json", "context", "order_state", "query"]
    )
    return prompt, example_json

# 互動式點餐對話
def interactive_ordering():
    cus_choice = {"加蛋": 10, "起司": 10, "泡菜": 10, '燒肉': 20, '起司牛奶': 5, '山型丹麥': 10}
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