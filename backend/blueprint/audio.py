from fastapi import HTTPException, UploadFile, File, APIRouter
from google.cloud import speech
from pydub import AudioSegment
from pathlib import Path
import shutil
import logging
import os

audio = APIRouter()

@audio.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=await file.read())
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=16000,
            language_code="zh-TW",
        )

        response = client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript

        return {"transcript": transcript}
    
    except Exception as e:
        logger.error(f"轉錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"轉錄失敗: {str(e)}")
    finally:
        file.file.close()

# 設置上傳目錄
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 設置臨時 WAV 檔案目錄
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@audio.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    # 檢查檔案格式
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="僅支持音頻檔案")

    try:
        # 保存上傳的檔案
        webm_path = UPLOAD_DIR / file.filename
        with webm_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 將 WebM 轉換為 WAV（LINEAR16，16 位元，16000 Hz，單聲道）
        wav_path = TEMP_DIR / f"{file.filename}.wav"
        audio = AudioSegment.from_file(webm_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 2 bytes = 16 bits
        audio.export(wav_path, format="wav")

        # 讀取 WAV 檔案內容
        with wav_path.open("rb") as audio_file:
            audio_content = audio_file.read()

        # 驗證音頻檔案資訊
        logger.info(f"音頻檔案: {wav_path}, 大小: {len(audio_content)} bytes")

        # 配置 Google Speech-to-Text
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="zh-TW",  # 繁體中文，可改為 "en-US" 等
            enable_automatic_punctuation=True,
        )
        audio = speech.RecognitionAudio(content=audio_content)

        # 發送語音轉文字請求
        response = client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript

        if not transcript:
            logger.warning("未檢測到語音內容")
            return {
                "message": "音頻上傳成功，但未檢測到語音內容",
                "filename": file.filename,
                "transcript": ""
            }

        # 返回結果
        logger.info(f"轉錄結果: {transcript}")
        return {
            "message": "音頻上傳成功並轉錄",
            "filename": file.filename,
            "transcript": transcript
        }

    except Exception as e:
        logger.error(f"處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理失敗: {str(e)}")
    finally:
        file.file.close()
        # 清理臨時檔案
        if wav_path.exists():
            try:
                os.remove(wav_path)
                logger.info(f"已刪除臨時檔案: {wav_path}")
            except Exception as e:
                logger.error(f"刪除臨時檔案失敗: {str(e)}")