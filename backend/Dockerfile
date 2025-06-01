# 使用官方的 Python 映像檔
FROM python:3.11.11

# 設定工作目錄
WORKDIR /app/backend

# 複製 requirements.txt
COPY requirements.txt ./

# 安裝 Python 依賴項
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有後端程式碼
COPY . .

# 暴露 FastAPI 應用程式的埠口 (FastAPI 預設運行在 8000 埠)
EXPOSE 8000

# 啟動 FastAPI 應用程式
# 使用 gunicorn 運行 uvicorn 是一個推薦的生產部署方式
# 將 your_app_name 替換為您的 FastAPI 應用程式實例所在的檔案名 (例如：main.py -> main)
# 將 app 替換為您的 FastAPI 應用程式實例的變數名 (例如：app = FastAPI() -> app)
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]