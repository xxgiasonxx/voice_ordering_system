# Flask API 部署點餐系統
from flask import Flask, request, send_file
from voice_ordering import process_voice_order
import os

app = Flask(__name__)

@app.route('/order', methods=['POST'])
def order():
    if 'audio' not in request.files:
        return {"error": "請上傳語音檔案"}, 400
    
    audio_file = request.files['audio']
    audio_path = "temp_input.wav"
    audio_file.save(audio_path)

    # 處理語音訂單
    try:
        output_audio = process_voice_order(audio_path)
        return send_file(output_audio, mimetype='audio/mpeg')
    finally:
        # 清理臨時檔案
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(output_audio):
            os.remove(output_audio)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)