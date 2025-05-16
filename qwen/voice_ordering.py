# 語音點餐系統（整合 Whisper 和 gTTS）
import whisper
from gtts import gTTS
import os
from qwen.rag_mcdonalds import load_menu_to_vectorstore, rag_query

# 初始化 Whisper 模型
whisper_model = whisper.load_model("base")

# 語音轉文字
def speech_to_text(audio_file):
    result = whisper_model.transcribe(audio_file)
    return result["text"]

# 文字轉語音
def text_to_speech(text, output_file="response.mp3"):
    tts = gTTS(text=text, lang="zh-TW")
    tts.save(output_file)
    return output_file

# 語音點餐流程
def process_voice_order(audio_file):
    # 轉語音為文字
    user_query = speech_to_text(audio_file)
    print(f"用戶說: {user_query}")

    # 用 RAG 檢索並生成回應
    vectorstore = load_menu_to_vectorstore()
    response = rag_query(user_query, vectorstore)
    print(f"助手回: {response}")

    # 轉回應為語音
    audio_output = text_to_speech(response)
    return audio_output

if __name__ == "__main__":
    # 假設有錄好的語音輸入
    audio_file = "user_input.wav"  # 請錄製語音檔案
    output_audio = process_voice_order(audio_file)
    print(f"語音回應已儲存至: {output_audio}")