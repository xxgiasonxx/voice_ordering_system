import yaml
import json

# 讀取 YAML 檔案
with open('nlu.yml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# 定義 system prompt，讓模型知道它是點餐助手
system_message = "你是一個麥當勞點餐助手，幫用戶快速點餐、確認訂單、回答菜單問題。用台灣口語，親切又專業！"

# 轉換成 Qwen3 對話格式
conversations = []
for intent in data['nlu']:
    intent_name = intent['intent']
    for example in intent['examples'].split('\n'):
        example = example.strip('- ').strip()
        if not example:
            continue
        # 模擬 assistant 回應（根據意圖自訂）
        if intent_name == 'order_food':
            response = f"好的，{example} 幫你記下來！要不要升級套餐？"
        elif intent_name == 'specify_size':
            response = f"OK，{example}，還有什麼可以幫你的？"
        elif intent_name == 'ask_menu_item':
            response = "我們有大麥克、麥香雞、薯條、雞塊，飲料有可樂、紅茶、咖啡。你想點啥？"
        elif intent_name == 'confirm_order':
            response = "訂單確認囉！請問是外帶還是內用？"
        elif intent_name == 'checkout':
            response = "好的，總共是 XXX 元，請問用現金還是行動支付？"
        else:
            response = "可以再說一次嗎？我幫你搞定！"

        # 建立對話結構
        conversation = {
            "id": f"{intent_name}_{len(conversations)}",
            "conversations": [
                {"from": "system", "value": system_message},
                {"from": "user", "value": example},
                {"from": "assistant", "value": response}
            ]
        }
        conversations.append(conversation)

# 儲存成 JSON
with open('qwen3_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(conversations, f, ensure_ascii=False, indent=2)

print("資料集轉換完成！")