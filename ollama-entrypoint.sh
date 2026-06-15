#!/bin/sh
set -e

# 1. 在背景啟動臨時的 ollama serve 用來下載模型
ollama serve &
OLLAMA_PID=$!

echo "[Ollama] 等待服務啟動..."
# 💡 核心修正：移除 curl，改用內建的 ollama list 檢查 API 服務是否準備好
for i in $(seq 1 120); do
    if ollama list > /dev/null 2>&1; then
        echo "[Ollama] 服務已啟動!"
        break
    fi
    if [ $i -eq 120 ]; then
        echo "[Ollama] 等待超時，服務可能未正確啟動"
        exit 1
    fi
    sleep 1
done

echo "[Ollama] 檢查並拉取模型..."

# 檢查與拉取 qwen2.5:1.5b
if ! ollama list | awk '{print $1}' | grep -Fxq "qwen2.5:1.5b"; then
    echo "[Ollama] 正在下載 qwen2.5:1.5b..."
    ollama pull qwen2.5:1.5b || echo "[警告] qwen2.5:1.5b 下載失敗..."
else
    echo "[Ollama] qwen2.5:1.5b 已存在，跳過下載。"
fi

# 檢查與拉取 qwen3-embedding:0.6b
if ! ollama list | awk '{print $1}' | grep -Fxq "qwen3-embedding:0.6b"; then
    echo "[Ollama] 正在下載 qwen3-embedding:0.6b..."
    ollama pull qwen3-embedding:0.6b || echo "[警告] qwen3-embedding:0.6b 下載失敗..."
else
    echo "[Ollama] qwen3-embedding:0.6b 已存在，跳過下載。"
fi

echo "[Ollama] 模型初始化檢查完備。正在切換至前景運行..."

kill $OLLAMA_PID
wait $OLLAMA_PID

# 讓 ollama 真正成為 PID 1 接管容器
exec ollama serve
