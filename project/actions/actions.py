import sqlite3
import os
import requests # for Qwen LLM API
from typing import Any, Text, Dict, List, Optional, Tuple

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted, FollowupAction, ActiveLoop

DATABASE_NAME = os.getenv("DATABASE_URL", "mcdonalds_menu.db") # 允許透過環境變數設定
QWEN_API_URL = os.getenv("QWEN_API_URL", "YOUR_QWEN3_API_ENDPOINT_HERE")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "YOUR_QWEN3_API_KEY_IF_NEEDED")

# --- 資料庫輔助函數 ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # 結果可以當字典用
    return conn

def query_db(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def find_item_in_db(item_name_input: str) -> Optional[sqlite3.Row]:
    """根據輸入名稱查找標準餐點 (精確名稱或別名)"""
    # 首先嘗試完全匹配標準名稱
    exact_match = query_db("SELECT * FROM menu_items WHERE name = ? AND is_available = TRUE", (item_name_input,))
    if exact_match:
        return exact_match[0]
    
    # 然後嘗試模糊匹配標準名稱或別名
    # 注意：LIKE 查詢可能需要更複雜的相似度算法或 LLM 輔助以提高準確性
    # 這裡的 LIKE 比較基礎，主要用於別名包含
    # 如果 item_name_input 包含多個詞，這個 LIKE 可能不夠好
    # 例如：用戶說 "大薯條"，資料庫 food_name "薯條"，aliases "Fries"
    # 可以考慮將 item_name_input 分詞後再查詢，或主要依賴 NLU 的 food_name_lookup
    
    # 這裡假設 NLU 已經做得不錯，或者 item_name_input 是 lookup table 裡的值
    # 若 NLU 抓取的 food_name 是 "大薯"，但資料庫標準是 "薯條"，則需要轉換
    # 較好的做法是，NLU 盡可能抓取標準 food_name (透過 lookup table 或訓練)
    
    # 為簡化，假設 item_name_input 接近標準名或在 aliases 中
    items = query_db("SELECT * FROM menu_items WHERE (name LIKE ? OR aliases LIKE ?) AND is_available = TRUE", 
                     (f"%{item_name_input}%", f"%{item_name_input}%"))
    if items:
        # 如果有多個匹配，這裡可以加入澄清邏輯，或預設返回第一個
        # 對於更精確的匹配，可以考慮 Levenshtein 距離等，或完全依賴 NLU 的 lookup 結果
        return items[0] # 簡單返回第一個，真實場景需優化
    return None

def parse_quantity_modifier(modifier: Optional[str], default: int = 1) -> int:
    """從 '六塊', '兩份' 等解析出數字"""
    if not modifier:
        return default
    num_map = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for zh_num, val in num_map.items():
        if zh_num in modifier:
            return val
    # 嘗試直接轉換數字
    try:
        import re
        num_str = re.findall(r'\d+', modifier)
        if num_str:
            return int(num_str[0])
    except:
        pass
    return default

# --- 核心 Actions ---
class ActionAddToCart(Action):
    def name(self) -> Text:
        return "action_add_to_cart"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        food_name_input = tracker.get_slot("extracted_food_name")
        quantity_input = tracker.get_slot("extracted_quantity") # "一", "兩", "1", "2"
        size_input = tracker.get_slot("extracted_size") # "大", "中", "小"
        quantity_modifier_input = tracker.get_slot("extracted_quantity_modifier") # "六塊", "兩份"

        events = []

        if not food_name_input:
            dispatcher.utter_message(text="抱歉，我不知道您想點什麼耶。")
            return [SlotSet("extracted_food_name", None), SlotSet("extracted_quantity", None), SlotSet("extracted_size", None), SlotSet("extracted_quantity_modifier", None)]

        # 處理 food_name_input 可能包含大小的情況，例如 "大薯"
        # 這裡的邏輯可以非常複雜，依賴於 NLU 的標註方式
        # 簡單假設：如果 NLU 標註了 food_name 和 size (如 "大薯" -> food_name:"薯條", size:"大")
        # 或者 NLU 直接標註 food_name:"大薯"，然後在這裡嘗試解析
        
        # 為了簡化，我們主要依賴 NLU 的 food_name 實體 (假設已透過 lookup table 趨近標準)
        # 和獨立的 size, quantity 實體

        item_in_db = find_item_in_db(food_name_input)

        if not item_in_db:
            dispatcher.utter_message(response="utter_item_not_found_in_db", item_name=food_name_input)
            return [SlotSet("extracted_food_name", None), SlotSet("extracted_quantity", None), SlotSet("extracted_size", None), SlotSet("extracted_quantity_modifier", None)]

        db_item_name = item_in_db["name"]
        db_price = item_in_db["price"]
        db_stock = item_in_db["stock_quantity"]
        db_is_available = item_in_db["is_available"]
        db_available_sizes = item_in_db["available_sizes"].split(',') if item_in_db["available_sizes"] else []
        db_default_size = item_in_db["default_size"] if item_in_db["default_size"] else (db_available_sizes[0] if db_available_sizes else None)


        if not db_is_available:
            dispatcher.utter_message(response="utter_item_not_available_general", item_name=db_item_name)
            return [SlotSet("extracted_food_name", None), SlotSet("extracted_quantity", None), SlotSet("extracted_size", None), SlotSet("extracted_quantity_modifier", None)]

        # 處理數量
        quantity = parse_quantity_modifier(quantity_modifier_input, default=1) # 優先處理 "六塊雞塊"
        if quantity_input: # 如果有獨立的 quantity 實體
            try:
                num_map = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
                quantity = num_map.get(quantity_input, int(quantity_input))
            except ValueError:
                quantity = 1 # 解析失敗則預設為1

        if db_stock is not None and db_stock > 0 and quantity > db_stock: # 有限庫存且不足
            dispatcher.utter_message(text=f"哎呀，「{db_item_name}」庫存只剩下 {db_stock} 份了，不夠 {quantity} 份喔。")
            return [SlotSet("extracted_food_name", None), SlotSet("extracted_quantity", None), SlotSet("extracted_size", None), SlotSet("extracted_quantity_modifier", None)]
        
        # 處理大小
        chosen_size = None
        if db_available_sizes: # 如果該品項有大小之分
            if size_input and size_input in db_available_sizes:
                chosen_size = size_input
            elif size_input: # 指定了大小，但無效
                 dispatcher.utter_message(text=f"不好意思，「{db_item_name}」沒有「{size_input}」的選項，可選的大小有：{', '.join(db_available_sizes)}。請問您要哪個大小？")
                 events.append(SlotSet("extracted_food_name", db_item_name)) # 保留品項，等待用戶提供有效大小
                 events.append(SlotSet("extracted_size", None))
                 return events # 等待用戶修正大小
            else: # 未指定大小，使用預設
                chosen_size = db_default_size
        
        # 如果 chosen_size 仍然是 None 但 db_available_sizes 有值，表示需要詢問大小
        if db_available_sizes and not chosen_size:
            dispatcher.utter_message(text=f"請問「{db_item_name}」您需要什麼大小呢？有 {', '.join(db_available_sizes)} 可以選。")
            events.append(SlotSet("extracted_food_name", db_item_name)) # 保留品項，等待用戶提供大小
            return events

        # 更新購物車
        shopping_cart = tracker.get_slot("shopping_cart") or []
        
        # 檢查購物車中是否已有相同品項 (同名同大小)
        item_found_in_cart = False
        for cart_item in shopping_cart:
            if cart_item["name"] == db_item_name and cart_item.get("size") == chosen_size:
                cart_item["quantity"] += quantity
                item_found_in_cart = True
                break
        
        if not item_found_in_cart:
            cart_entry = {
                "id": item_in_db["id"], # 資料庫中的ID
                "name": db_item_name,
                "quantity": quantity,
                "price_per_unit": db_price, # 單位價格
                "size": chosen_size if chosen_size else None,
            }
            shopping_cart.append(cart_entry)
        
        events.append(SlotSet("shopping_cart", shopping_cart))
        
        item_name_with_details = f"{quantity}份 "
        if chosen_size:
            item_name_with_details += f"{chosen_size} "
        item_name_with_details += db_item_name

        dispatcher.utter_message(response="utter_item_added_to_cart", item_name_with_details=item_name_with_details)
        
        # 清空臨時槽位
        events.extend([
            SlotSet("extracted_food_name", None),
            SlotSet("extracted_quantity", None),
            SlotSet("extracted_size", None),
            SlotSet("extracted_quantity_modifier", None),
            SlotSet("extracted_option", None)
        ])
        return events

class ActionShowCart(Action):
    def name(self) -> Text:
        return "action_show_cart"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        shopping_cart = tracker.get_slot("shopping_cart") or []
        if not shopping_cart:
            dispatcher.utter_message(response="utter_cart_is_empty")
            return []

        cart_summary_parts = []
        total_price = 0
        for item in shopping_cart:
            size_str = f"({item['size']})" if item['size'] else ""
            item_total_price = item['quantity'] * item['price_per_unit']
            cart_summary_parts.append(f"{item['name']}{size_str} x {item['quantity']} = {item_total_price}元")
            total_price += item_total_price
        
        cart_summary = "\n- ".join(cart_summary_parts)
        if cart_summary:
             cart_summary = "- " + cart_summary # 加上第一個項目符號

        dispatcher.utter_message(response="utter_show_cart_contents", cart_summary=cart_summary, total_price=str(round(total_price,1)))
        return []

class ActionRemoveFromCart(Action):
    def name(self) -> Text:
        return "action_remove_from_cart"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        food_name_to_remove = tracker.get_slot("extracted_food_name")
        shopping_cart = tracker.get_slot("shopping_cart") or []
        events = [SlotSet("extracted_food_name", None)] # 清除槽位

        if not food_name_to_remove:
            dispatcher.utter_message(text="請問您想移除哪個餐點呢？")
            return events
        
        # 嘗試從資料庫找到標準名稱，以應對用戶說的是別名
        item_in_db = find_item_in_db(food_name_to_remove)
        standard_name_to_remove = item_in_db["name"] if item_in_db else food_name_to_remove

        original_cart_len = len(shopping_cart)
        # 移除時，如果有多個不同大小的同名品項，需要更精確的指定，或預設移除第一個匹配的
        # 為簡化，這裡只比較標準名稱
        new_shopping_cart = [item for item in shopping_cart if item["name"] != standard_name_to_remove]

        if len(new_shopping_cart) < original_cart_len:
            dispatcher.utter_message(response="utter_item_removed_from_cart", item_name=standard_name_to_remove)
            events.append(SlotSet("shopping_cart", new_shopping_cart))
        else:
            dispatcher.utter_message(response="utter_cannot_remove_item_not_in_cart", item_name=food_name_to_remove)
            
        return events

class ActionCheckout(Action):
    def name(self) -> Text:
        return "action_checkout"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        shopping_cart = tracker.get_slot("shopping_cart") or []
        if not shopping_cart:
            dispatcher.utter_message(response="utter_cart_is_empty")
            dispatcher.utter_message(response="utter_ask_order") # 提醒用戶點餐
            return []

        total_price = 0
        for item in shopping_cart:
            total_price += item['quantity'] * item['price_per_unit']
        
        dispatcher.utter_message(response="utter_checkout_prompt_with_total", total_price=str(round(total_price,1)))
        # 在真實系統中，這裡可能會有等待用戶確認 (affirm/deny) 的流程
        # 為了簡化，我們假設用戶說結帳就是要結帳了
        # dispatcher.utter_message(response="utter_order_confirmed_thank_you")
        # events = [SlotSet("shopping_cart", [])] # 清空購物車
        # return events
        # 讓 utter_checkout_prompt_with_total 後由用戶 affirm/deny 決定是否清空
        return []
    
class ActionConfirmCheckoutAndClearCart(Action): # 如果用戶在 utter_checkout_prompt_with_total 後 affirm
    def name(self) -> Text:
        return "action_confirm_checkout_and_clear_cart"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_order_confirmed_thank_you")
        return [SlotSet("shopping_cart", [])] # 清空購物車

class ActionShowCategoryItems(Action):
    def name(self) -> Text:
        return "action_show_category_items"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        category_name = tracker.get_slot("extracted_menu_category")
        events = [SlotSet("extracted_menu_category", None)]

        if not category_name:
            dispatcher.utter_message(text="請問您想查詢哪個餐點類別呢？")
            return events

        # 這裡的 category_name 可能需要先標準化，例如 "漢堡類" -> "漢堡"
        # 假設 NLU 的 lookup table 或訓練已處理
        items = query_db("SELECT name, price FROM menu_items WHERE category = ? AND is_available = TRUE ORDER BY name", (category_name,))

        if items:
            items_list_str = ", ".join([f"{item['name']} ({item['price']}元)" for item in items])
            dispatcher.utter_message(response="utter_inform_category_items", category_name=category_name, items_list=items_list_str)
        else:
            dispatcher.utter_message(response="utter_category_not_found", category_name=category_name)
        return events

class ActionShowItemDetails(Action):
    def name(self) -> Text:
        return "action_show_item_details"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        food_name_input = tracker.get_slot("extracted_food_name")
        events = [SlotSet("extracted_food_name", None)]

        if not food_name_input:
            dispatcher.utter_message(text="請問您想查詢哪個餐點的資訊呢？")
            return events
        
        item_in_db = find_item_in_db(food_name_input)

        if item_in_db:
            desc = item_in_db["description"] if item_in_db["description"] else ""
            sizes = f"可選大小: {item_in_db['available_sizes']}。" if item_in_db["available_sizes"] else ""
            
            message = f"{item_in_db['name']}，價格是 {item_in_db['price']}元。{sizes} {desc}"
            dispatcher.utter_message(text=message.strip())
            # dispatcher.utter_message(response="utter_inform_item_details", 
            #                          item_name=item_in_db["name"], 
            #                          price=str(item_in_db["price"]),
            #                          description=(item_in_db["description"] if item_in_db["description"] else ""))
        else:
            dispatcher.utter_message(response="utter_item_not_found_in_db", item_name=food_name_input)
        return events
    
class ActionUpdateLastItemQuantity(Action):
    def name(self) -> Text:
        return "action_update_last_item_quantity"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        shopping_cart = tracker.get_slot("shopping_cart") or []
        new_quantity_input = tracker.get_slot("extracted_quantity")
        events = [SlotSet("extracted_quantity", None)] # 清空槽位

        if not shopping_cart:
            dispatcher.utter_message(text="您的購物車還是空的喔，沒辦法修改數量。")
            return events
        
        if not new_quantity_input:
            dispatcher.utter_message(text="請問您想把最後一個品項的數量改成多少呢？")
            return events
        
        try:
            num_map = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
            new_quantity = num_map.get(new_quantity_input, int(new_quantity_input))
            if new_quantity <= 0:
                dispatcher.utter_message(text="數量必須大於0喔。如果您想移除該品項，可以說「移除XXX」。")
                return events
        except ValueError:
            dispatcher.utter_message(text="抱歉，我不太明白您說的數量。")
            return events

        last_item = shopping_cart[-1]
        
        # 檢查庫存 (假設最後一項是從資料庫來的，有庫存資訊)
        item_in_db = query_db("SELECT stock_quantity FROM menu_items WHERE id = ?", (last_item["id"],))
        if item_in_db and item_in_db[0]["stock_quantity"] is not None and item_in_db[0]["stock_quantity"] > 0 and new_quantity > item_in_db[0]["stock_quantity"]:
            dispatcher.utter_message(text=f"哎呀，「{last_item['name']}」庫存只剩下 {item_in_db[0]['stock_quantity']} 份了，不夠 {new_quantity} 份喔。")
            return events

        old_quantity = last_item["quantity"]
        last_item["quantity"] = new_quantity
        
        dispatcher.utter_message(text=f"好的，已將「{last_item['name']}」的數量從 {old_quantity} 改為 {new_quantity}。")
        events.append(SlotSet("shopping_cart", shopping_cart))
        
        # 詢問是否還有其他需求
        # dispatcher.utter_message(response="utter_ask_what_else") # 可選
        return events

# --- Qwen LLM Fallback Action ---
class ActionQwenFallback(Action):
    def name(self) -> Text:
        return "action_qwen_fallback"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        last_user_message = tracker.latest_message.get("text")
        dispatcher.utter_message(text=f"嗯...關於「{last_user_message}」，我正在思考一下...")

        if not QWEN_API_URL or QWEN_API_URL == "YOUR_QWEN3_API_ENDPOINT_HERE":
            dispatcher.utter_message(text="Qwen LLM API 未設定，無法進一步處理模糊查詢。")
            dispatcher.utter_message(response="utter_default_qwen_fallback_prompt")
            return [UserUtteranceReverted()] # 允許 Rasa 的其他 fallback 機制或規則處理

        # 構建給 Qwen 的 prompt
        # 這裡的 prompt 非常關鍵，需要引導 Qwen 針對麥當勞點餐場景進行理解和修正
        # 也可以考慮將購物車內容或部分對話歷史加入 context
        current_cart = tracker.get_slot("shopping_cart") or []
        cart_context = ""
        if current_cart:
            cart_items_str = ", ".join([f"{item['quantity']}份{item.get('size','')}{item['name']}" for item in current_cart])
            cart_context = f"顧客目前的購物車裡有：{cart_items_str}。"
        
        # 更精細的 prompt，引導 LLM 輸出 Rasa 能理解的意圖或澄清後的指令
        # 例如，可以讓 LLM 嘗試輸出 JSON 格式的意圖和實體
        system_prompt = (
            "你是一個協助台灣麥當勞語音點餐系統的AI助手。"
            "你的任務是理解顧客可能模糊不清、口語化或帶有錯字的指令。"
            "請根據對話上下文和顧客說的話，判斷顧客最可能的意圖和想點的餐點/選項。"
            "如果能明確判斷，請嘗試將顧客的話修正為更清晰的點餐指令。"
            "例如，如果顧客說「大賣」，你應該理解為「大麥克」。如果顧客說「可已」，應理解為「可以」。"
            "如果顧客說「那個雞的漢堡，不要辣的」，你可能需要結合菜單知識判斷是「麥香雞」或「嫩煎雞腿堡」。"
            "如果無法判斷或修正，請回答「無法判斷」。"
        )
        
        user_prompt = f"{cart_context} 顧客說了：「{last_user_message}」。請問這在點餐情境下最有可能的意思或想點的標準餐點名稱是什麼？"

        payload = {
            "model": "qwen_0.6b_chat", # 或你的模型名稱
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 80,
            "temperature": 0.3 
        }
        headers = {"Content-Type": "application/json"}
        if QWEN_API_KEY and QWEN_API_KEY != "YOUR_QWEN3_API_KEY_IF_NEEDED":
            headers["Authorization"] = f"Bearer {QWEN_API_KEY}"
        
        qwen_suggestion = ""
        try:
            response = requests.post(QWEN_API_URL, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            qwen_result = response.json()
            
            if qwen_result.get("choices") and qwen_result["choices"][0].get("message"):
                qwen_suggestion = qwen_result["choices"][0]["message"]["content"].strip()
            else:
                print(f"Qwen API response format unexpected: {qwen_result}")
                qwen_suggestion = "無法判斷"

        except requests.exceptions.RequestException as e:
            print(f"Error calling Qwen API: {e}")
            qwen_suggestion = "無法判斷" # 或其他錯誤處理
        except Exception as e:
            print(f"An unexpected error occurred processing Qwen response: {e}")
            qwen_suggestion = "無法判斷"

        if qwen_suggestion and "無法判斷" not in qwen_suggestion and qwen_suggestion.lower() != last_user_message.lower():
            # Qwen3 提供了有意義的修正或解釋
            # 方案1: 直接詢問用戶
            # dispatcher.utter_message(text=f"請問您的意思是不是：「{qwen_suggestion}」？")
            # return [UserUtteranceReverted()] # 等待用戶確認或否認

            # 方案2: 將 LLM 的建議作為新的用戶輸入重新處理 (更自動化)
            # 需要小心 LLM 的輸出是否真的能被 Rasa NLU 正確解析
            dispatcher.utter_message(text=f"我猜您的意思可能是：「{qwen_suggestion}」？我會試著這樣處理看看。")
            # 將 LLM 的建議存入 slot，並觸發一個新的 user utterance event
            # 這有點像用戶自己說了 LLM 的建議
            return [
                SlotSet("qwen_clarified_text", qwen_suggestion),
                UserUtteranceReverted(), # 先回退 NLU fallback
                # 重新觸發一個用戶訊息，Rasa 會重新跑 NLU pipeline
                # 但 FollowupAction("action_listen") 後直接發送 UserUtterance 可能會有問題
                # 較穩定的方式是讓 Rasa 自己重新監聽，或用其他事件觸發
                # 另一種方式：如果 LLM 能輸出標準意圖+實體，則直接觸發對應 Action 或設定槽位
                # 此處簡化：先讓 Rasa 重新監聽，Qwen 的建議僅供參考或由其他規則利用 qwen_clarified_text slot
                 FollowupAction("action_listen") # 讓 Rasa 重新聆聽，或者接下來有個 rule 處理 qwen_clarified_text
            ]

        else:
            # Qwen3 無法提供有意義的幫助
            dispatcher.utter_message(response="utter_default_qwen_fallback_prompt")
            return [UserUtteranceReverted()]