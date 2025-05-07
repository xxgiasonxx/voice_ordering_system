from flask import Flask, jsonify, request
from rasa.core.agent import Agent
import asyncio
# from google.cloud import speech_v1p1beta1 as speech
import pyaudio
import queue
import threading

app = Flask(__name__)
agent = Agent.load("models/rasa_model.tar.gz")

RATE = 16000
CHUNK = int(RATE / 10)

# def stream_audio(q):
#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
#     while True:
#         data = stream.read(CHUNK, exception_on_overflow=False)
#         q.put(data)
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

# def speech_to_text():
#     client = speech.SpeechClient()
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=RATE,
#         language_code="zh-TW",
#     )
#     streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
#     q = queue.Queue()
#     threading.Thread(target=stream_audio, args=(q,), daemon=True).start()

#     def generate_requests():
#         while True:
#             yield speech.StreamingRecognizeRequest(audio_content=q.get())

#     responses = client.streaming_recognize(streaming_config, generate_requests())
#     for response in responses:
#         for result in response.results:
#             if result.is_final:
#                 return result.alternatives[0].transcript
#     return ""

@app.route("/order", methods=["POST"])
async def process_order():
    # 從 POST 請求的 JSON 主體中獲取數據
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "請求主體中缺少 'text'"}), 400

    text = data['text'] # 從請求數據中獲取 text

    if not text: # 檢查文本是否為空
        return jsonify({"error": "文本不能為空"}), 400

    response = await agent.handle_text(text)
    print(response)
    intent = response[0].get("intent", {})
    entities = response[0].get("entities", [])
    message = response[0].get("text", "抱歉，我無法理解您的請求。")
    return jsonify({"text": text, "intent": intent, "entities": entities, "response": message})

if __name__ == "__main__":
    app.run(debug=True)