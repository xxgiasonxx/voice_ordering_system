# 語音點餐系統

早餐店語音點餐系統：顧客按住按鈕用中文說出想吃的餐點，系統辨識語音、理解需求，自動把品項加入購物車並用台灣早餐店的口吻回覆。也可以用傳統菜單點餐。全部模型都在本機執行，不需要雲端 API。

## 功能特色

- **按住說話點餐**：按住麥克風按鈕說話、放開後整句辨識，一次說多個品項也可以（例如「我要一份薯條跟一個火腿吐司，還有一杯大杯古早奶茶」）
- **聽錯字也能點對**：語音辨識常把「火腿」聽成「活推」，系統會用拼音比對菜單，仍然點到「吐司-火腿」
- **品項不會亂對**：LLM 只負責理解語意並輸出品項名稱，品項 ID 與價格一律由程式從資料庫查出
- **全程繁體中文**：語音辨識與 LLM 偶爾輸出的簡體字會自動轉成台灣繁體
- **雙模式操作**：語音點餐與傳統菜單點餐共用同一個購物車

## 技術架構

| 層面 | 技術 |
|------|------|
| 前端 | React + TypeScript + Vite（Nginx 提供靜態檔） |
| 後端 | FastAPI (Python 3.10) |
| 語音辨識 | [moonshine-ai/moonshine-streaming-tiny-zh](https://huggingface.co/moonshine-ai/moonshine-streaming-tiny-zh)（27M 參數，在後端以 CPU 執行） |
| LLM | Ollama + `qwen3:1.7b`（關閉思考模式） |
| Embedding | Ollama + `qwen3-embedding:0.6b` |
| 資料庫 | PostgreSQL 16（菜單）+ Redis（訂單與對話 session）+ ChromaDB（菜單向量檢索） |
| 容器化 | Docker Compose |

### 語音點餐流程

```
按住按鈕說話 ──► 前端每 256ms 傳送 16kHz PCM 音訊（WebSocket /asr）
                   │  說話途中每 2 秒回傳即時字幕
放開按鈕 ────────► 前端送出 end_utterance
                   ▼
後端 Moonshine 辨識整段語音 → 轉繁體
                   ▼
程式用「字面 + 拼音」比對顧客提到的菜單品項（例如 活推吐司 → 吐司-火腿）
                   ▼
qwen3:1.7b 讀取：比對結果 + 最相關的 10 筆菜單 + 目前訂單
輸出：```sys``` 品項名稱與數量、```cus``` 給顧客的回覆
                   ▼
程式把品項名稱對應回資料庫 ID 與價格 → 更新 Redis 訂單 → 回傳前端
```

更完整的說明請見 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 快速啟動

### 環境需求

- Docker Desktop（Windows 需啟用 WSL2）或 Docker Engine + Compose
- 記憶體 8 GB 以上
- **麥克風**：Mac mini 等沒有內建麥克風的電腦，需要接有麥克風的耳機或外接麥克風

### 啟動

```bash
cd voice_ordering_system
docker compose up -d --build
```

**第一次啟動會比較久**，請耐心等候：

1. Ollama 下載 `qwen3:1.7b` 與 `qwen3-embedding:0.6b`（共約 2 GB）。**後端會等模型下載完才啟動**，這段期間 `docker compose ps` 看到後端還沒起來是正常的。
2. 後端容器建立後第一次啟動時，從 Hugging Face 下載 Moonshine 語音模型（約 100 MB；快取沒有掛 volume，重建容器後會再下載一次）。
3. 後端發現資料庫是空的，會**自動匯入菜單**（`morning_eat.xlsx` → PostgreSQL），不需要手動執行遷移。

確認狀態：

```bash
docker compose ps
docker compose logs -f backend   # 看到 "ASR model preloaded" 代表後端就緒
```

### 開始使用

1. 開啟 http://localhost （請從首頁進入；直接開啟 `/voiceorder` 等子頁面會 404）
2. 選擇語音點餐 → 點「開始說話點餐」→ 允許麥克風權限
3. **按住**麥克風按鈕說話，說完**放開**，等待回覆

### 有 NVIDIA GPU 的機器

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Mac 沒有 NVIDIA GPU，直接用 `docker compose up -d` 即可。

### 停止服務

```bash
docker compose down      # 保留模型與資料庫
docker compose down -v   # ⚠️ 連同 volume 一起刪除：下次啟動要重新下載約 2 GB 模型
```

## 效能

LLM 回覆時間主要取決於 Ollama 能不能用 GPU：

| 環境 | 每句回覆時間（實測） |
|------|------|
| Mac + Docker（Docker 無法使用 Mac GPU，Ollama 以 CPU 執行） | 約 11–14 秒（模型剛載入的第一句約 60 秒） |
| Mac 原生 Ollama（使用 Apple GPU） | 約 6 秒 |
| 語音辨識（Moonshine，CPU） | 約 0.1–0.5 秒 |

### 為什麼用 qwen3:1.7b

在內部 27 句點餐測試（含同音錯字）中比較，條件為 Docker CPU、菜單檢索 10 筆：

| 模型 | 準確率 | 每句平均 |
|------|------|------|
| **qwen3:1.7b** | **26–27 / 27** | 11–14 秒 |
| qwen3.5:0.8b | 21 / 27 | 約 8 秒 |
| qwen3:0.6b | 20 / 27 | 約 12 秒 |

較小的模型在 CPU 上沒有快多少（主要時間花在讀取 prompt），但會把「蘿蔔糕」點成蛋餅、漏掉飲料，或在顧客只是詢問時自行加點，因此不採用。

換模型只需修改 `docker-compose.yml` 的 `LLM_MODEL`，並在 `ollama-entrypoint.sh` 與 Ollama healthcheck 加上該模型。

## 環境變數

Docker 部署的設定都在 `docker-compose.yml`；本機開發可參考 `backend/.env.example`。

| 變數 | 說明 | Docker 預設值 |
|------|------|------|
| `LLM_MODEL` | Ollama 模型名稱，或 `gemini_api` 改用 Google Gemini | `qwen3:1.7b` |
| `OLLAMA_BASE_URL` | Ollama 服務位址 | `http://ollama:11434` |
| `ASR_MODEL` | Hugging Face 語音辨識模型 | `moonshine-ai/moonshine-streaming-tiny-zh` |
| `DB_URL` | PostgreSQL 連線字串；未設定時改用 `DB_PATH` 的 SQLite | `postgresql://postgres:postgres@postgres:5432/morning_eat` |
| `DB_PATH` | SQLite 菜單資料庫路徑（僅在沒有 `DB_URL` 時使用） | `./db/morning_eat.db` |
| `CHROMADB_PATH` | ChromaDB 菜單向量資料庫路徑 | `./db/chroma_db` |
| `REDIS_HOST` / `REDIS_PORT` | Redis 位址 | `redis` / `6379` |
| `SECRET_KEY` | JWT 簽章密鑰 | ⚠️ 需更換 |
| `FERNET_KEY` | Cookie 加密金鑰 | ⚠️ 需更換 |
| `TOKEN_EXPIRE_MINUTES` | Session 有效時間（分鐘） | `300` |
| `GOOGLE_API_KEY` | 只有 `LLM_MODEL=gemini_api` 時需要 | — |
| `HF_HOME` | Hugging Face 模型快取位置 | `/root/.cache/huggingface` |

**正式環境請務必更換 `SECRET_KEY` 與 `FERNET_KEY`。**

## API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/get-token` | 取得或更新 session（寫入 Cookie） |
| GET | `/me` | 驗證目前 session |
| GET | `/menu` | 完整菜單 |
| POST | `/order/add-item` | 加入購物車 |
| POST | `/order/update-item` | 更新數量 |
| POST | `/order/remove-item` | 移除品項 |
| POST | `/order/clear-cart` | 清空購物車 |
| POST | `/order/ordering` | 文字點餐（同語音點餐的 AI 流程） |
| WebSocket | `/asr` | 語音點餐（按住說話） |
| GET | `/history` | 語音點餐對話紀錄 |
| GET | `/see_order` | 目前訂單 |
| POST | `/submit_payment` | 送出付款 |
| POST | `/clean_cookie` | 清除 session |

請求與回應格式（含 WebSocket 訊息協定）請見 [docs/API.md](docs/API.md)。後端啟動後也可以在 http://localhost:8000/docs 測試 REST API。

## 專案結構

```
voice_ordering_system/
├── backend/
│   ├── app.py                   # FastAPI 入口：/menu、啟動時自動建資料庫、預載語音模型
│   ├── setup.py                 # 初始化 ChromaDB、資料庫連線、Redis
│   ├── blueprint/
│   │   ├── asr_stream.py        # WebSocket /asr：按住說話 → 語音辨識 → LLM
│   │   ├── order.py             # 購物車 REST API
│   │   ├── payment.py           # 訂單查詢、付款
│   │   └── token.py             # Session / Cookie
│   ├── rag/
│   │   ├── rag_morning_eat.py   # 點餐核心：品項比對、prompt、解析 LLM 輸出
│   │   ├── useModel.py          # LLM 設定（Ollama / Gemini）
│   │   └── CRUD_database.py     # 資料庫連線與查詢（PostgreSQL / SQLite）
│   ├── debug_and_migrate.py     # 菜單匯入：morning_eat.xlsx → SQLite → PostgreSQL
│   ├── morning_eat.xlsx         # 菜單原始資料
│   ├── db/                      # SQLite 菜單、ChromaDB 向量資料庫
│   ├── requirements_minimal.txt # Docker 使用的 Python 依賴
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── pages/VoiceOrder.tsx # 語音點餐頁（按住說話）
│       ├── pages/Menu.tsx       # 菜單點餐頁
│       └── ...
├── docs/                        # 詳細文件
├── docker-compose.yml           # 服務編排（CPU）
├── docker-compose.gpu.yml       # NVIDIA GPU 覆寫設定
└── ollama-entrypoint.sh         # Ollama 啟動時自動下載模型
```

## 開發

### 前端

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

> 後端 CORS 白名單目前沒有 `http://localhost:5173`，用開發伺服器時請在 `backend/app.py` 的 `allow_origins` 加上。

### 後端

```bash
docker compose up -d postgres redis ollama   # 先啟動依賴服務

cd backend
cp .env.example .env                         # 依需要修改
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements_minimal.txt
uvicorn app:app --reload --port 8000
```

> `pyproject.toml` / `uv.lock` 尚未同步最新依賴，目前請以 `requirements_minimal.txt` 為準。

完整說明請見 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

### 修改菜單

編輯 `backend/morning_eat.xlsx` 後重新匯入：

```bash
docker compose exec backend python debug_and_migrate.py
```

菜單的向量資料庫（ChromaDB）需另外用 `rebuild_vectorstore.py` 重建。

## 常見問題

| 狀況 | 原因與處理 |
|------|------|
| 說話後回覆「沒有收到聲音」，log 顯示 `peak=0.000` | 瀏覽器沒收到麥克風聲音：檢查 macOS「系統設定 → 隱私權與安全性 → 麥克風」是否允許瀏覽器，改完要 ⌘Q 重開瀏覽器；確認電腦有可用的麥克風 |
| 回覆很慢 | 見上方[效能](#效能)；Mac 的 Docker 無法使用 GPU |
| `model "..." not found` | Ollama 模型還沒下載完，等 `docker compose logs ollama` 顯示下載完成 |
| 每次啟動都要重新下載模型 | 停止時用了 `docker compose down -v`，改用 `docker compose down` |
| 直接開 `http://localhost/voiceorder` 顯示 404 | Nginx 未設定前端路由回退，請從首頁進入 |
| 回覆「系統出了點問題」 | 查看 `docker compose logs backend` 中的 `Ollama 推理失敗` 訊息 |

更多請見 [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)。

## License

MIT License
