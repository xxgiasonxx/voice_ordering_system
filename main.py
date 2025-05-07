import torch
from transformers import BertTokenizer, BertForSequenceClassification, BertForTokenClassification
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torchaudio
from gtts import gTTS
from flask import Flask, request, send_file
import os

# 初始化 Flask 應用
app = Flask(__name__)

# 載入語音轉文字模型（支援中文）
processor = Wav2Vec2Processor.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn")
model = Wav2Vec2ForCTC.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn")

# 定義菜單
MENU = {
    "牛肉漢堡": 100,
    "薯條": 50,
    "可樂": 30
}

# 載入BERT模型和tokenizer
intent_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
intent_model = BertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=2)  # 意圖：點餐、查詢
entity_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
entity_model = BertForTokenClassification.from_pretrained('bert-base-chinese', num_labels=3)  # 標籤：O, B-ITEM, I-ITEM

# 語音轉文字
def speech_to_text(audio_path):
    waveform, sample_rate = torchaudio.load(audio_path)
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    input_values = processor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt").input_values
    with torch.no_grad():
        logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    return transcription

# 意圖識別
def get_intent(text):
    inputs = intent_tokenizer(text, return_tensors="pt")
    outputs = intent_model(**inputs)
    logits = outputs.logits
    intent_id = torch.argmax(logits, dim=1).item()
    intents = ["點餐", "查詢"]
    return intents[intent_id]

# 實體抽取
def extract_entities(text):
    inputs = entity_tokenizer(text, return_tensors="pt")
    outputs = entity_model(**inputs)
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2)
    tokens = entity_tokenizer.convert_ids_to_tokens(inputs["input_ids"].squeeze().tolist())
    entities = []
    current_entity = ""
    for token, prediction in zip(tokens, predictions.squeeze().tolist()):
        if prediction == 1:  # B-ITEM
            if current_entity:
                entities.append(current_entity)
            current_entity = token
        elif prediction == 2:  # I-ITEM
            current_entity += token
        else:
            if current_entity:
                entities.append(current_entity)
                current_entity = ""
    if current_entity:
        entities.append(current_entity)
    return entities

# 解析數量（簡單示例）
def extract_quantity(text):
    if "兩" in text or "二" in text:
        return 2
    return 1  # 預設數量為1

# 解析訂單
def parse_order(text):
    intent = get_intent(text)
    if intent != "點餐":
        return None, "您想查詢菜單嗎？"
    
    entities = extract_entities(text)
    order = []
    quantity = extract_quantity(text)  # 提取數量
    for entity in entities:
        entity = entity.replace("##", "")  # 清理BERT分詞符號
        if entity in MENU:
            order.append({"item": entity, "quantity": quantity, "price": MENU[entity] * quantity})
    return order, None

# 文字轉語音
def text_to_speech(text, output_file="response.mp3"):
    tts = gTTS(text=text, lang='zh-tw')
    tts.save(output_file)
    return output_file

# Flask API 端點
@app.route("/order", methods=["POST"])
def process_order():
    if "audio" not in request.files:
        return {"error": "No audio file provided"}, 400
    
    audio_file = request.files["audio"]
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)
    
    text = speech_to_text(audio_path)
    if not text:
        response_text = "抱歉，我沒聽懂您的點餐，請再說一次。"
    else:
        order, query_response = parse_order(text)
        if query_response:
            response_text = query_response
        elif not order:
            response_text = "抱歉，我沒聽懂您的點餐，請再說一次。"
        else:
            total = sum(item["price"] for item in order)
            order_summary = ", ".join(f"{item['quantity']}份{item['item']}" for item in order)
            response_text = f"您的訂單是：{order_summary}，總金額 {total} 元。請確認是否正確。"
    
    output_audio = text_to_speech(response_text)
    return send_file(output_audio, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)