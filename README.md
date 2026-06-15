# 晨式吃早餐 - 語音點餐系統

一個現代化的語音點餐系統，使用 FastAPI 後端 + React 前端，支援語音辨識、智慧推薦和流暢的點餐體驗。

## 功能特色

- **語音點餐** - 透過麥克風以語音方式點餐，支援即時語音辨識
- **智慧推薦** - 基於 RAG (Retrieval-Augmented Generation) 技術，根據用戶需求推薦餐點
- **雙模式操作** - 支援語音和傳統選單點餐
- **即時反饋** - 清晰顯示訂單內容、價格和客製化選項
- **多語言支援** - AI 助理可用中文提供服務

## 技術架構

| 層面 | 技術 |
|------|------|
| 前端 | React + TypeScript + Vite |
| 後端 | FastAPI (Python 3.10) |
| 資料庫 | PostgreSQL 16 + Redis |
| AI 模型 | Qwen3-ASR (語音辨識) + Ollama (本地 LLM) |
| 向量資料庫 | ChromaDB |
| 容器化 | Docker + Docker Compose |

## 快速啟動

### 環境需求

- Docker Desktop (已啟用 WSL2/Linux 容器)
- Windows 10/11 或 Linux/macOS

### 啟動服務

```bash
# 克隆專案
cd voice_ordering_system

# 啟動所有服務
docker compose up -d

# 等待服務啟動 (約 2-3 分鐘首次啟動)
# 訪問 http://localhost 開始使用
```

### 驗證服務狀態

```bash
docker compose ps
```

所有服務正常運行時顯示 `Up` 狀態。

## 專案結構

```
voice_ordering_system/
├── backend/                    # FastAPI 後端
│   ├── blueprint/              # API 路由模組
│   │   ├── order.py           # 訂單相關端點
│   │   ├── payment.py         # 支付相關端點
│   │   ├── token.py           # 認證相關端點
│   │   └── asr_stream.py      # 語音串流處理
│   ├── rag/                    # RAG 系統
│   │   ├── rag_morning_eat.py # 點餐邏輯
│   │   └── CRUD_database.py   # 資料庫操作
│   ├── app.py                 # FastAPI 應用程式
│   └── setup.py               # 全域初始化
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/             # 頁面元件
│   │   ├── components/         # 共用元件
│   │   ├── contexts/           # React Context
│   │   ├── hooks/              # 自訂 Hooks
│   │   └── router/             # 路由設定
│   └── Dockerfile
├── docs/                       # 文件 (本資料夾)
├── docker-compose.yml         # 容器編排設定
└── README.md                   # 本檔案
```

## API 端點

### 認證

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/get-token` | 取得或更新 session token |
| GET | `/me` | 驗證當前 token 是否有效 |

### 菜單

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/menu` | 取得完整菜單 |

### 購物車 (REST)

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/order/add-item` | 新增商品至購物車 |
| POST | `/order/update-item` | 更新商品數量 |
| POST | `/order/remove-item` | 移除商品 |
| POST | `/order/clear-cart` | 清空購物車 |

### 訂單

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/order/ordering` | 語音點餐 (AI 處理) |
| GET | `/see_order` | 取得當前訂單狀態 |

### 支付

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/submit_payment` | 提交付款 |
| POST | `/clean_cookie` | 清除 session |

詳細 API 文件請參閱 [docs/API.md](API.md)。

## 環境變數

主要環境變數設定於 `docker-compose.yml`：

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `SECRET_KEY` | JWT 簽章密鑰 | (需自行設定) |
| `FERNET_KEY` | 資料加密金鑰 | (需自行設定) |
| `GOOGLE_API_KEY` | Gemini API 金鑰 | (需自行設定) |
| `OLLAMA_BASE_URL` | Ollama 服務位址 | `http://ollama:11434` |
| `DB_URL` | PostgreSQL 連線字串 | `postgresql://...` |

**重要**: 生產環境請更換預設的 `SECRET_KEY` 和 `FERNET_KEY`。

## 開發

### 前端開發

```bash
cd frontend
npm install
npm run dev
```

前端開發伺服器運行於 http://localhost:5173

### 後端開發

```bash
cd backend
# 使用 uv (推薦)
uv sync
uv run python app.py

# 或使用 Docker 掛載模式
docker compose up -d --build backend
```

後端 API 文件: http://localhost:8000/docs

### 資料庫遷移

```bash
# 重新執行資料庫遷移
docker compose exec backend python debug_and_migrate.py
```

## 故障排除

常見問題請參閱 [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

### 服務無法啟動

```bash
# 檢查容器日誌
docker compose logs backend
docker compose logs postgres
docker compose logs redis

# 重啟服務
docker compose restart
```

### 前端顯示網路錯誤

1. 確認後端已啟動且運行於 8000 連接埠
2. 清除瀏覽器快取 (Ctrl+Shift+Del)
3. 確認 CORS 設定正確

### 語音辨識無回應

1. 確認麥克風權限已授權
2. 檢查 Ollama 服務是否正常
3. 查看 ASR 模型是否已下載

## License

MIT License