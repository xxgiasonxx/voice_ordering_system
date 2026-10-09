# 開發指南

本指南適用於要在本機開發或修改本系統的開發者。只是要跑起來用，請看 [README](../README.md) 的快速啟動。

## 前置需求

- Python 3.10
- Node.js 18+ / npm 9+
- Docker Desktop（用來跑 PostgreSQL、Redis、Ollama）
- 麥克風（測試語音點餐）

## 1. 啟動依賴服務

```bash
docker compose up -d postgres redis ollama
docker compose ps    # ollama 變成 healthy 代表模型下載完成
```

## 前端開發

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173，支援熱重載
```

| 指令 | 說明 |
|------|------|
| `npm run dev` | 開發伺服器 |
| `npm run build` | 型別檢查（`tsc -b`）+ 建構生產版本 |
| `npm run lint` | ESLint |
| `npm run preview` | 預覽建構結果 |

注意事項：

- 後端 CORS 白名單（`backend/app.py` 的 `allow_origins`）目前只有 `http://localhost`、`:80`、`:3000`，用 5173 開發時請加上 `http://localhost:5173`
- 語音頁的 WebSocket 位址寫死為 `ws://localhost:8000/asr`（`src/pages/VoiceOrder.tsx`）
- REST API 位址來自 `VITE_BACKEND_API_URL` / `VITE_API_BASE_URL`，預設 `http://localhost:8000`

### 前端目錄結構

```
frontend/src/
├── pages/
│   ├── Home.tsx          # 首頁
│   ├── Choice.tsx        # 選擇語音 / 菜單點餐
│   ├── Menu.tsx          # 菜單點餐
│   ├── VoiceOrder.tsx    # 語音點餐（按住說話、WebSocket）
│   ├── OrderState.tsx    # 訂單狀態
│   ├── OrderView.tsx     # 購物車
│   └── Payment.tsx       # 結帳
├── components/           # Header、Icon、DesignSystem
├── contexts/
│   └── TokenContext.tsx  # Session 管理
├── hooks/                # useAudioRecorder、useWebSocket（目前沒有頁面使用）
└── router/router.tsx     # 路由
```

## 後端開發

### 安裝依賴

```bash
cd backend
python3.10 -m venv .venv && source .venv/bin/activate

# 先裝 CPU 版 PyTorch（不加 index-url 在 Linux 上會裝到數 GB 的 CUDA 版）
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements_minimal.txt
```

> `requirements_minimal.txt` 是 Docker 實際使用的依賴清單。`pyproject.toml` / `uv.lock` 與 `requirements.txt` 都尚未同步（缺少 transformers、opencc、pypinyin 等），目前請不要用 `uv sync`。

### 環境變數

```bash
cp .env.example .env
```

`.env.example` 已設定成連到 `docker compose` 啟動的本機服務（`localhost`）。重點：

| 變數 | 說明 |
|------|------|
| `LLM_MODEL` | **一定要設定**。程式在未設定時預設為 `gemini_api`（需要 Google API key） |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `DB_URL` | 設定時用 PostgreSQL；註解掉則用 `DB_PATH` 的 SQLite（`./db/morning_eat.db`，不需 PostgreSQL） |
| `REDIS_HOST` | `localhost` |

### 執行

```bash
uvicorn app:app --reload --port 8000
```

- 第一次執行會從 Hugging Face 下載 Moonshine 語音模型（約 100 MB）
- 使用 PostgreSQL 且資料庫是空的時，會自動匯入菜單
- API 文件：http://localhost:8000/docs

### 後端目錄結構

```
backend/
├── app.py                  # FastAPI 入口：/menu、自動建資料庫、預載語音模型
├── setup.py                # 初始化 embedding、ChromaDB、資料庫連線、Redis
├── blueprint/
│   ├── asr_stream.py       # WebSocket /asr、/history：語音辨識 → LLM
│   ├── order.py            # 購物車 REST API、/order/ordering
│   ├── payment.py          # /see_order、付款
│   └── token.py            # Session / Cookie
├── rag/
│   ├── rag_morning_eat.py  # 點餐核心（品項比對、prompt、解析）
│   ├── useModel.py         # LLM 設定
│   └── CRUD_database.py    # 資料庫連線與查詢
├── interface/              # 回應格式定義
├── debug_and_migrate.py    # 菜單匯入 xlsx → SQLite → PostgreSQL
├── rebuild_vectorstore.py  # 重建 ChromaDB 菜單向量
├── download_model.py       # 預先下載 Moonshine 模型
├── morning_eat.xlsx        # 菜單原始資料
└── requirements_minimal.txt
```

## 修改點餐邏輯

點餐理解的流程見 [ARCHITECTURE.md](ARCHITECTURE.md#3-點餐理解ragrag_morning_eatpy)。常見的修改位置：

| 想改的東西 | 位置 |
|------|------|
| 店員的語氣、回覆規則、範例 | `rag/rag_morning_eat.py` 的 `create_prompt_template()` |
| 每次給 LLM 的菜單筆數（目前 10 筆） | `rag/rag_morning_eat.py` 的 `similarity_search(query, k=10)` |
| 品項比對規則（拼音、同名品項） | `rag/rag_morning_eat.py` 的 `find_mentioned_items()` |
| LLM 名稱對應回菜單的規則 | `rag/rag_morning_eat.py` 的 `resolve_item()` |
| LLM 參數（context 長度、溫度、思考模式） | `rag/useModel.py` |
| 加料價格 | `rag/rag_morning_eat.py` 的 `cus_choice`（`order_real_time()`）與 `setup.py` |
| 錄音、按住說話行為 | `frontend/src/pages/VoiceOrder.tsx` |
| 語音辨識、即時字幕間隔 | `blueprint/asr_stream.py`（`PARTIAL_BYTES` 等常數） |

> 調整 prompt 或菜單筆數後，請用多種句子實測準確率與速度。檢索 50 筆時 CPU 上每句要 30 秒以上；小於 1.7B 的模型準確率明顯下降。

### 更換 LLM

1. 修改 `docker-compose.yml` 的 `LLM_MODEL`
2. 在 `ollama-entrypoint.sh` 加上下載該模型的步驟
3. 在 `docker-compose.yml` 的 ollama healthcheck 加上該模型名稱

任何 Ollama 模型名稱都可以直接使用（`useModel.py` 會把 `gemini_api` 以外的名稱都當成 Ollama 模型）。

## 修改菜單

1. 編輯 `backend/morning_eat.xlsx`
2. 匯入資料庫（會清空並重建 PostgreSQL 菜單資料表）：
   ```bash
   DB_URL=postgresql://postgres:postgres@localhost:5432/morning_eat python debug_and_migrate.py
   ```
3. 重建向量資料庫：
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434 python rebuild_vectorstore.py
   ```

> 這兩個腳本不會讀取 `.env`，連線位址要用環境變數指定；沒指定時會連到 Docker 內部的主機名稱（`postgres`、`ollama`），在本機會連線失敗。

## 資料庫操作

```bash
# 連線到 PostgreSQL
docker compose exec postgres psql -U postgres -d morning_eat
```

```sql
SELECT * FROM main_menu LIMIT 5;
SELECT id, name, "M", "L" FROM drink_item;   -- M / L 要加雙引號
SELECT * FROM combo_menu;
```

## AI 模型

```bash
# 預先下載 Moonshine 語音模型
python download_model.py

# 查看 / 下載 Ollama 模型
docker compose exec ollama ollama list
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec ollama ollama pull qwen3-embedding:0.6b
```

## 偵錯

### 語音點餐

後端 log 每句會印出：

```
ASR (2.4s, peak=0.596): '我要一份玉米蛋餅'
LLM (11.2s): '好喔，台式蛋餅-玉米 40 元！...'
```

- `peak` 是音量峰值（0～1）：接近 0 代表沒收到聲音，正常說話約 0.1～0.9
- 辨識結果為空 `''` 而 peak 正常：語音太短或太小聲
- 出現 `找不到對應品項：...`：LLM 輸出的品項名稱對不到菜單
- 出現 `Ollama 推理失敗：...`：後面接著實際錯誤原因

### 常用檢查

```bash
curl http://localhost:8000/menu          # 資料庫
curl http://localhost:11434/api/tags     # Ollama 模型
docker compose exec backend python -c "from setup import redis_client; print(redis_client.ping())"
```

### 測試腳本

`backend/` 下有幾個手動測試腳本（`test_api.py`、`test_cart_api.py`、`test_llm_direct.py`、`test_rag_llm.py`），直接用 `python <檔名>` 執行。

`test_asr.py` 是 pytest 測試，但**目前已過時無法執行**：它匯入的 `create_wav_header`、`raw_pcm_to_wav`、`AudioBuffer` 已不存在於 `asr_stream.py`。

## 提交規範

```
<type>: <subject>

<body>
```

類型：feat、fix、docs、style、refactor、test、chore
