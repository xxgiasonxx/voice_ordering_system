# 語音點餐系統 — 後端

FastAPI 後端：語音辨識（Moonshine）、點餐理解（Ollama qwen3:1.7b + RAG）、購物車與付款 API。

專案整體說明與快速啟動請見[根目錄 README](../README.md)，架構請見 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)。

## 本機執行

```bash
# 依賴服務
docker compose up -d postgres redis ollama   # 在專案根目錄執行

# Python 3.10
python3.10 -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements_minimal.txt

cp .env.example .env
uvicorn app:app --reload --port 8000
```

- `requirements_minimal.txt` 是 Docker 實際使用的依賴；`pyproject.toml`、`uv.lock`、`requirements.txt` 尚未同步，請勿使用 `uv sync`
- `.env` 一定要有 `LLM_MODEL`（未設定時預設為 `gemini_api`）
- API 文件：http://localhost:8000/docs

詳見 [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md)。

## 主要檔案

| 檔案 | 說明 |
|------|------|
| `app.py` | 入口：`/menu`、啟動時自動匯入菜單、預載語音模型 |
| `blueprint/asr_stream.py` | WebSocket `/asr`：按住說話 → 語音辨識 → LLM |
| `rag/rag_morning_eat.py` | 點餐核心：品項比對、prompt、解析 LLM 輸出 |
| `rag/useModel.py` | LLM 設定 |
| `debug_and_migrate.py` | 菜單匯入 `morning_eat.xlsx` → SQLite → PostgreSQL |

## 已知限制

- 只支援中文
- 語音辨識模型很小，同音字錯誤常見（點餐時會用拼音比對菜單補救）
- LLM 回覆文字中的價格偶爾與實際訂單不一致（訂單內容與金額以程式計算為準）
- 在沒有 GPU 的環境每句回覆約 11–14 秒
