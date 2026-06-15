# 開發指南

本指南適用於希望在本地進行開發或修改本系統的開發者。

## 開發環境設定

### 前置需求

- Python 3.10+
- Node.js 18+
- npm 9+
- Docker Desktop (或 Docker Engine)
- Git

### 1. 複製專案

```bash
git clone <repo-url>
cd voice_ordering_system
```

### 2. 啟動基礎服務

```bash
# 啟動資料庫、Redis、Ollama
docker compose up -d postgres redis ollama

# 確認服務運行
docker compose ps
```

## 前端開發

### 環境設定

```bash
cd frontend

# 安裝依賴
npm install

# 複製環境變數
cp .env.example .env.local  # 如有需要
```

### 開發模式

```bash
# 啟動開發伺服器 (支援熱重載)
npm run dev

# 或使用 Docker 掛載模式
# 修改代碼即時反映
```

前端運行於 http://localhost:5173

### 建構生產版本

```bash
npm run build

# 預覽建構結果
npm run preview
```

### 程式碼規範

```bash
# 程式碼檢查
npm run lint

# 類型檢查
npm run typecheck
```

### 前端目錄結構

```
frontend/src/
├── pages/               # 頁面元件
│   ├── Home.tsx        # 首頁
│   ├── Menu.tsx        # 菜單頁
│   ├── VoiceOrder.tsx  # 語音點餐
│   ├── OrderView.tsx   # 訂單檢視
│   └── Payment.tsx     # 結帳頁面
├── components/         # 共用元件
│   ├── DesignSystem.tsx  # 設計系統
│   ├── Header.tsx        # 頁面標頭
│   └── Icon.tsx          # 圖示
├── contexts/           # React Context
│   └── TokenContext.tsx  # Token 管理
├── hooks/              # 自訂 Hooks
│   ├── useAudioRecorder.ts  # 錄音功能
│   └── useWebSocket.ts      # WebSocket
└── router/
    └── router.tsx       # 路由設定
```

## 後端開發

### 環境設定

```bash
cd backend

# 使用 uv (推薦)
pip install uv
uv sync

# 或使用傳統 pip
pip install -r requirements.txt
```

### 環境變數

建立 `backend/.env` 檔案：

```env
SECRET_KEY=your-development-secret-key
FERNET_KEY=your-development-fernet-key
REDIS_HOST=localhost
REDIS_PORT=6379
DB_URL=postgresql://postgres:postgres@localhost:5432/morning_eat
OLLAMA_BASE_URL=http://localhost:11434
GOOGLE_API_KEY=your-google-api-key
```

### 本地執行

```bash
# 直接執行 (需要先啟動 PostgreSQL, Redis, Ollama)
python app.py

# 或使用 uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### API 文件

後端運行後，存取 http://localhost:8000/docs 查看 Swagger UI 文件。

### 後端目錄結構

```
backend/
├── blueprint/           # API 路由模組
│   ├── order.py         # 訂單相關
│   ├── payment.py       # 支付相關
│   ├── token.py         # 認證相關
│   └── asr_stream.py    # 語音串流
├── rag/                 # RAG 系統
│   ├── rag_morning_eat.py  # 點餐邏輯
│   ├── useModel.py         # 模型使用
│   └── CRUD_database.py    # 資料庫操作
├── interface/           # 介面定義
├── app.py              # FastAPI 應用程式
├── setup.py            # 全域初始化
└── requirements.txt    # 依賴列表
```

### 測試

```bash
# 執行所有測試
pytest

# 執行特定測試
pytest tests/test_order.py -v

# 單一端點測試
python test_cart_api.py
```

## 資料庫操作

### 連線到 PostgreSQL

```bash
# 使用 Docker
docker compose exec postgres psql -U postgres -d morning_eat

# 或使用 pgcli
pgcli postgresql://postgres:postgres@localhost:5432/morning_eat
```

### 常用 SQL

```sql
-- 查詢所有主餐
SELECT * FROM main_menu LIMIT 5;

-- 查詢所有飲料
SELECT * FROM drink_item;

-- 查詢套餐
SELECT * FROM combo_menu;

-- 統計資料筆數
SELECT COUNT(*) FROM main_menu;
SELECT COUNT(*) FROM drink_item;
```

### 執行遷移

```bash
# 重新遷移資料庫
python debug_and_migrate.py
```

## AI 模型

### 下載 ASR 模型

```bash
python download_model.py
```

### 下載 Ollama 模型

```bash
# 進入 Ollama 容器
docker compose exec ollama bash

# 下載模型
ollama pull qwen2.5:1.5b
ollama pull qwen3-embedding:0.6b
```

### 測試 Ollama

```bash
docker compose exec ollama ollama list
docker compose exec ollama ollama show qwen2.5:1.5b
```

## 偵錯技巧

### 前端偵錯

1. **React DevTools** - 安裝瀏覽器擴充功能
2. **Network** - 檢查 API 請求/回應
3. **Console** - 查看日誌輸出

### 後端偵錯

1. **PDB** - 在程式碼中加入 `import pdb; pdb.set_trace()`
2. **Logging** - 查看 `docker compose logs backend`
3. **Swagger** - http://localhost:8000/docs 測試 API

### 常見偵錯端點

```bash
# 測試資料庫連線
curl http://localhost:8000/menu

# 測試 Token
curl -v http://localhost:8000/me

# 測試 Redis
docker compose exec backend python -c "from setup import redis_client; print(redis_client.ping())"
```

## 代碼貢獻流程

1. **Fork** 本專案
2. **建立分支** `git checkout -b feature/your-feature`
3. **Commit** 變更 `git commit -am 'Add some feature'`
4. **Push** 到分支 `git push origin feature/your-feature`
5. **建立 Pull Request**

### 提交訊息規範

```
<type>: <subject>

<body>

<footer>
```

類型：feat, fix, docs, style, refactor, test, chore