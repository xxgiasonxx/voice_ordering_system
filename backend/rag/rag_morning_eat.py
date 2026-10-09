# File: rag_retrieval.py
# 晨間廚房語音點餐系統，基於 morning_eat.xlsx，LLM 回傳類別-品項名稱給系統（程式對應回 id），顧客用自然語言，生成 JSON 訂單並匯出
from langchain_core.prompts import PromptTemplate
from .CRUD_database import query_name_to_price, query_all_menu
from .useModel import useModel
from sqlite3 import Connection
from difflib import SequenceMatcher
from dotenv import load_dotenv
from opencc import OpenCC
from pypinyin import lazy_pinyin
import os
import re

load_dotenv()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini_api")
# 小模型偶爾輸出簡體字，統一轉成台灣繁體（介面顯示與菜單比對都用繁體）
_s2tw = OpenCC("s2tw")


# 初始化訂單
def init_order_state():
    return {
        "items": [],
        "total_price": 0,
        "status": "ongoing"
    }

# RAG 檢索 + LLM 生成回應 + 解析訂單
def rag_query(query, conversation_history, vectorstore, order_state, cus_choice, conn):
    # 檢索相關菜單
    try:
        # 只取最相關 10 筆：顧客提到的品項另由 find_mentioned_items 比對，菜單太長會讓 CPU 推論慢好幾倍
        docs = vectorstore.similarity_search(query, k=10)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"RAG 檢索失敗：{e}")
        context = "暫無菜單資訊"

    prompt, ex_json = create_prompt_template()

    # 用 Ollama 生成回應
    try:
        model = useModel(LLM_MODEL)

        chain = prompt | model

        matched = find_mentioned_items(query, conn)
        matched_text = "、".join(f"{item['class']}-{item['name']}" for item in matched) or "無"
        response = chain.invoke({'json': ex_json, 'history': conversation_history, 'context': context, 'order_state': order_state, 'query': query, 'matched': matched_text})

        if hasattr(response, 'content'):
            response = response.content
        elif not isinstance(response, str):
            response = str(response)

        # 解析 LLM 回應，更新訂單
        customer_response, new_order_state = parse_llm_response(response, order_state, cus_choice, conn, matched)
        return customer_response, new_order_state
    except Exception as e:
        print(f"Ollama 推理失敗：{e}")
        return "不好意思，系統出了點問題，可以再說一次你的需求嗎？", order_state

def find_mentioned_items(query, conn):
    """從顧客原話直接比對菜單，找出明確提到的品項，給 LLM 當優先候選"""
    # 語音辨識常出現同音錯字（火腿→活推），所以字面或拼音其中一個對上就算提到
    query_py = "|" + "|".join(lazy_pinyin(query)) + "|"

    def said(text):
        text = re.sub(r"\s*[（(].*?[)）]", "", text)  # 去掉「(1片)」這類備註
        return text in query or ("|" + "|".join(lazy_pinyin(text)) + "|") in query_py

    menu = query_all_menu(conn)
    name_count = {}
    for item in menu:
        name_count[item["name"]] = name_count.get(item["name"], 0) + 1
    found = []
    for item in menu:
        cls, name = item.get("class", ""), item["name"]
        if cls == "套餐":
            hit = said(f"{name}套餐")
        else:
            # 同名品項（例如蛋餅-火腿、吐司-火腿）要連類別一起提到才算
            hit = said(name) and (name_count[name] == 1 or said(cls) or said(cls.replace("台式", "")))
        if hit:
            found.append(item)
    # 只保留最長的比對（「黃金豬排堡」優先於「黃金豬排」）
    return [a for a in found if not any(a["name"] != b["name"] and a["name"] in b["name"] for b in found)]

def resolve_item(text, conn):
    """把 LLM 輸出的「類別-品項名稱」對應到菜單品項：先完全比對，再模糊比對"""
    def norm(s):
        return re.sub(r"[\s\-－_()（）]", "", str(s))

    target = norm(text)
    menu = query_all_menu(conn)
    # 類別寫錯但品名正確（例如「台式蛋餅-麥克雞塊」），品名唯一時直接採用
    name_part = norm(re.split(r"[-－]", str(text))[-1])
    same_name = [i for i in menu if norm(i["name"]) == name_part] or [i for i in menu if norm(i["name"]).startswith(name_part)]
    if len(same_name) == 1 and not any(target == norm(i.get("class", "") + i["name"]) for i in menu):
        return same_name[0]
    best, best_score = {}, 0.0
    for item in menu:
        cls, name = item.get("class", ""), item.get("name", "")
        # 顧客常省略「台式」，或把類別放在品名後面（火腿吐司）
        short_cls = cls.replace("台式", "")
        variants = {norm(cls + name), norm(name + cls), norm(short_cls + name), norm(name + short_cls)}
        if cls == "特調飲品":
            variants.add(norm(name))
        if cls == "套餐":
            variants |= {norm(name + "套餐"), norm(item.get("id", ""))}
        if target in variants:
            return item
        score = max(SequenceMatcher(None, target, v).ratio() for v in variants)
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= 0.6 else {}

def query_price(cls: str, name: str, conn: Connection):
    result = query_name_to_price(conn, cls, name)
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
    if status == "+":
        item_price = deal_with_price(item, customizations)
        for existing_item in order_state["items"]:
            if existing_item['item_id'] == item['id'] and existing_item['customization']['note'] == customizations:
                existing_item['quantity'] += quantity
                order_state['total_price'] += existing_item['subtotal'] * quantity
                return order_state
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

def parse_llm_response(response, order_state, cus_choice, conn, matched=()):
    # 找到sys和cus的區塊
    response = _s2tw.convert(response).replace("臺", "台")
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
            intent = line.split(": ")[1].strip()
            order_state["status"] = intent
        if line.startswith("+"):
            # 格式：+ <類別-品項名稱> <數量> <客製化>，品名可能含空白（例如「大火腿片 (1片)」）
            match = re.match(r"^\+\s*(.+?)\s+(\d+)\s*(.*)$", line)
            if not match:
                continue
            name, quantity, cus = match.groups()
            result = resolve_item(name, conn)
            if not result:
                print(f"找不到對應品項：{name}")
                continue
            # LLM 選到同名但不同類別的品項（例如顧客說火腿吐司，LLM 寫台式蛋餅-火腿），以顧客原話比對結果為準
            if result not in matched:
                result = next((m for m in matched if m["name"] == result["name"]), result)
            cus, cus_price = deal_with_cus(cus or "無", cus_choice)
            order_state = change_order(order_state, "+", result, int(quantity), cus, cus_price)
        if line.startswith("-"):
            action, item_id, quantity = line.split()
            order_state = change_order(order_state, action, item_id, int(quantity))
    return cus_content, order_state

def create_prompt_template():
    example_json = {
          "items": [
              {
                "id": 12131,
                "item_id": 1,
                "class": "台式蛋餅",
                "name": "原味",
                "unitPrice": 30,
                "subtotal": 65,
                "quantity": 1,
                "customization": {
                    "cus_price": 35,
                    "note": "雙蛋、起司、泡菜",
                }
              }
            ],
          "total_price": 65,
          "status": "ongoing"
    }
    template = '''
    你是一個晨間廚房早餐店店員，負責幫顧客快速點餐、確認訂單、回答菜單問題，態度要親切、熱情，像在台灣早餐店櫃檯服務一樣！用戶可能因語音辨識錯誤，你要自己想辦法猜回來，嘗試用語音角度理解可能的正確詞彙，你的任務是根據顧客的自然語言查詢、菜單資訊和當前訂單狀態，生成兩部分純文字回應：
    1. **給系統**：這輪顧客點了什麼或刪除了什麼品項的「類別-品項名稱」及數量，以及客製化內容。
    2. **給顧客**：親切的台灣口語回應，包含完整品項名稱、價格（用 OO 元標示）、客製等。

    ---

    ### 指令

    #### 1. 給系統（類別-品項名稱及數量）
    - 從顧客查詢和菜單資訊提取品項，輸出「類別-品項名稱」及數量，類別和品項名稱必須**一字不差照抄菜單資訊**（飲料類別為「特調飲品」，套餐類別為「套餐」）。
    - 先確認顧客說的類別（蛋餅、吐司、漢堡、厚片…）再找品項，例如「火腿吐司」是「吐司-火腿」，不是「台式蛋餅-火腿」；「古早奶茶」不是「古早紅茶」。
    - **格式**：
      - **新增**：`+ <類別-品項名稱> <數量> <客製化>`（例如 `+ 台式蛋餅-原味 1 無` 表示台式蛋餅-原味 1 份，無客製）。
      - **取消**：`- <訂單id> <數量>`（例如 `- 12313 1` 表示取消訂單中 id 1 品項 1 份）。
      - **每行一個動作**，無動作時留空。
      - **客製化**：列出所有客製選項（例如 `雙蛋、起司、泡菜`），若無客製則填 `無`。僅記錄菜單資訊中可用的客製選項（例如雙蛋、起司、泡菜、無糖、去冰、少冰、加糖、中杯、大杯）。
    - **意圖**：
      - **點餐 (order)**：提取品項名稱和數量（例如「我要一份蛋餅」→ `+ 台式蛋餅-原味 1 無`）。
      - **取消 (cancel)**：識別取消品項（例如「蛋餅不要了」→ `- 12323 1`）。
      - **查詢菜單 (query)**：不輸出 id（例如「有什麼飲料？」）。
      - **確認訂單 (view_cus)**：不輸出 id，僅生成顧客回應，確認一次就好，如果顧客說確定就跳結束對話。
      - **結束對話 (end)**：不輸出 id，僅生成顧客回應、不要輸出訂單。
      - **找不到品項 (unknown)**：輸出 `系統：無對應品項`。
    - **數量處理**：
      - 未明確數量（例如「我要蛋餅」），假設 1 份。
      - 明確數量（例如「兩份蛋餅」），使用指定數量。
    - **模糊輸入**：
      - 若查詢模糊（例如「蛋餅」），選「台式蛋餅-原味」。
      - 若查詢多品項（例如「青花椒堡，大冰紅」），逐一提取品項名稱和數量。
    - **套餐**：
      - 若提到「A」「B」「C」「D」，選對應套餐（例如「A套餐」為 `套餐-A`）。
      - 若點主餐+套餐（例如「蛋餅 A套餐」），記錄主餐和套餐兩行。

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
      - 若提到「大冰紅」，選古早紅茶大杯（`特調飲品-古早紅茶`，L大杯 30 元）。
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
    + <類別-品項名稱> <數量> <客製化>
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
      + 台式蛋餅-原味 1 無
      ```
      ```cus
      好喔，台式蛋餅-原味 30 元！要加起司、泡菜，還是套餐？
      ```
      ```

    2. **查詢**：玉米蛋餅加起司加泡菜加雙蛋
      ```
      ```sys
      intent: order
      + 台式蛋餅-玉米 1 雙蛋、起司、泡菜
      ```
      ```cus
      好啦，台式蛋餅-玉米 加起司、泡菜、雙蛋 40 元！要不要加個套餐？
      ```
      ```

    3. **查詢**：青花椒堡，大冰紅
      ```
      ```sys
      intent: order
      + 漢堡-青花椒豬堡 1 無
      + 特調飲品-古早紅茶 1 大杯
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
      + 台式蛋餅-原味 1 無
      + 套餐-A 1 無
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

    ### 對話紀錄 (JSON 格式)
    {history}

    ### 開始吧！
    根據顧客查詢、菜單資訊和訂單狀態，生成給系統的類別-品項名稱及數量，以及給顧客的親切回應！
    - **菜單資訊**: {context}
    - **當前訂單狀態**: {order_state}
    - **用戶查詢**: {query}
    - **系統比對到顧客提到的品項（點餐時請優先照抄這些名稱）**: {matched}

      '''
    prompt = PromptTemplate(
        template=template,
        input_variables=["json", "history", "context", "order_state", "query", "matched"]
    )
    return prompt, example_json

def order_real_time(query: str, conversation_history, vectorstore, order_state, cus_choice, conn):
    cus_choice = {"加蛋": 10, "起司": 10, "泡菜": 10, '燒肉': 20, '起司牛奶': 5, '山型丹麥': 10}
    response, order_state = rag_query(query, conversation_history, vectorstore, order_state, cus_choice, conn)
    return response, order_state