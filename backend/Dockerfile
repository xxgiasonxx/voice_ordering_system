FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# 後端只用 CPU 跑 Moonshine（LLM 在 Ollama 容器），裝 CPU 版 torch，省掉數 GB 的 CUDA 套件
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

ENV HF_HOME=/root/.cache/huggingface
ENV PYTHONUNBUFFERED=1

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]