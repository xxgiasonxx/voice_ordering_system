import pyaudio
import wave
import numpy as np
import whisper
import os
import time
from threading import Event

# 錄音參數
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SEGMENT_DURATION = 2  # 每段錄音秒數
SILENCE_THRESHOLD = 500  # 無聲閾值
SILENCE_LIMIT = 6  # 連續無聲秒數，結束錄音
WAVE_OUTPUT_FILENAME = "temp_speech.wav"

class RealtimeSpeechToText:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.model = whisper.load_model("base")
        self.stop_event = Event()
        self.transcribed_text = ""

    def record_segment(self, stream, duration):
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            if self.stop_event.is_set():
                break
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        return frames

    def save_segment(self, frames):
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def is_silent(self, frames):
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data**2))
        return rms < SILENCE_THRESHOLD

    def transcribe_segment(self):
        if not os.path.exists(WAVE_OUTPUT_FILENAME):
            print("錯誤：音訊檔案未生成")
            return ""
        try:
            result = self.model.transcribe(WAVE_OUTPUT_FILENAME, language="zh")
            return result["text"]
        except Exception as e:
            print(f"轉錄失敗：{e}")
            return ""

    def display_text(self, text):
        if text:
            self.transcribed_text += " " + text
            # 清空當前行並顯示最新文字
            print("\r" + " " * 100, end="", flush=True)
            print(f"\r即時文字：{self.transcribed_text}", end="", flush=True)

    def run(self):
        stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("開始即時語音轉文字，請說話（說「結束」或保持沉默 6 秒以停止）...")
        
        silence_counter = 0
        
        while not self.stop_event.is_set():
            frames = self.record_segment(stream, SEGMENT_DURATION)
            
            if self.is_silent(frames):
                silence_counter += SEGMENT_DURATION
                if silence_counter >= SILENCE_LIMIT:
                    print("\n偵測到長時間無聲，結束轉錄")
                    self.stop_event.set()
                    break
            else:
                silence_counter = 0
            
            self.save_segment(frames)
            text = self.transcribe_segment()
            if text:
                print()  # 換行以顯示新文字
                self.display_text(text)
                if "結束" in text:
                    print("\n偵測到「結束」指令，停止轉錄")
                    self.stop_event.set()
                    break
            
            if os.path.exists(WAVE_OUTPUT_FILENAME):
                os.remove(WAVE_OUTPUT_FILENAME)
        
        stream.stop_stream()
        stream.close()
        self.p.terminate()
        
        print("\n最終轉錄結果：")
        print(self.transcribed_text if self.transcribed_text else "無轉錄內容")

def main():
    speech_to_text = RealtimeSpeechToText()
    speech_to_text.run()

if __name__ == "__main__":
    main()