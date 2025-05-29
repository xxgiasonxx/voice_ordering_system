from fastapi import APIRouter, WebSocket
from faster_whisper import WhisperModel
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn
from TTS.api import TTS
import soundfile as sf
import io
import numpy as np
from scipy import signal
import requests
import asyncio

audioWS = APIRouter()

# 初始化 Faster Whisper（Cpu，啟用 Silero VAD）
whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
)

# 初始化 Coqui TTS
tts_model = TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC-GST", progress_bar=False)

# 對話歷史
conversation_history = []

# 假設的 LLM 呼叫函數（可替換為 Gemini、OpenAI 或本地模型）
def call_llm(text: str) -> str:
    response, order_state = order_real_time(
        text, 
        vectorstore=vectorstore, 
        cus_choice=cus_choice, 
        order_state=order_state, 
        conn=conn
    )
    return response

@audioWS.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = io.BytesIO()
    session_start_time = asyncio.get_event_loop().time()
    MAX_SESSION_DURATION = 600  # 5 分鐘最大會話時間

    while True:
        try:
            # 檢查會話超時
            if asyncio.get_event_loop().time() - session_start_time > MAX_SESSION_DURATION:
                await websocket.send_json({"error": "會話超時，請重新開始"})
                await websocket.close()
                break

            # 接收音訊分段
            audio_data = await websocket.receive_bytes()
            audio_buffer.write(audio_data)
            audio_buffer.seek(0)

            # 讀取音訊並確保 16kHz
            audio, sample_rate = sf.read(audio_buffer)
            if sample_rate != 16000:
                audio = signal.resample(audio, int(len(audio) * 16000 / sample_rate))

            # Faster Whisper 轉錄（使用 Silero VAD）
            segments, _ = whisper_model.transcribe(
                audio,
                language="zh",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                # hotwords=["珍奶", "牛肉麵", "滷肉飯", "burger", "latte"]
            )
            transcript = " ".join(segment.text for segment in segments)
            audio_buffer = io.BytesIO()  # 重置緩衝區

            if transcript:
                conversation_history.append({"role": "user", "content": transcript})

                # 呼叫 LLM
                # llm_response = call_llm(transcript)
                llm_response = transcript
                print(transcript)
                conversation_history.append({"role": "assistant", "content": llm_response})

                # 生成語音回應
                audio_buffer = io.BytesIO()
                wav = tts_model.tts(text=llm_response, language="zh-CN")
                sf.write(audio_buffer, wav, 22050, format="WAV")
                audio_buffer.seek(0)

                # 傳送轉錄和語音回應
                await websocket.send_json({"text": transcript, "response": llm_response})
                await websocket.send_bytes(audio_buffer.getvalue())

        except Exception as e:
            await websocket.send_json({"error": str(e)})
            break