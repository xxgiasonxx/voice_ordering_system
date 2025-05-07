from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from unsloth import FastLanguageModel

# 載入微調後的模型
model, tokenizer = FastLanguageModel.from_pretrained(
    "./qwen3_finetuned",
    load_in_4bit=True,
    dtype=torch.bfloat16,
)

# 模擬點餐對話
def generate_response(user_input):
    messages = [
        {"role": "system", "content": "你是一個麥當勞點餐助手，幫用戶快速點餐、確認訂單、回答菜單問題。用台灣口語，親切又專業！"},
        {"role": "user", "content": user_input}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=512)
    response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response

# 測試範例
test_inputs = [
    "我要一個大麥克",
    "薯條可以炸久一點嗎？",
    "有什麼飲料？",
    "幫我結帳",
]
for input_text in test_inputs:
    print(f"用戶: {input_text}")
    print(f"助手: {generate_response(input_text)}")
    print("-" * 50)