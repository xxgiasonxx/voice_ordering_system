# 系統架構

## 整體架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         客戶端 (瀏覽器)                           │
│                      http://localhost:80                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Network                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend   │  │   Backend    │  │    Redis     │           │
│  │   (React)    │◄─┤  (FastAPI)   │◄─┤   (Cache)    │           │
│  │   :80        │  │   :8000      │  │   :6379      │           │
│  └──────────────┘  └──────┬───────┘  └──────────────┘           │
│                          │                                      │
│                          ▼                                      │
│                  ┌──────────────┐                                │
│                  │  PostgreSQL  │                                │
│                  │    :5432     │                                │
│                  └──────────────┘                                │
│                          │                                      │
│                          ▼                                      │
│                  ┌──────────────┐                                │
│                  │    Ollama    │                                │
│                  │   (AI/ASR)   │                                │
│                  │   :11434     │                                │
│                  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## 技術棧

### 前端 (Frontend)

- **框架**: React 18 + TypeScript
- **建構工具**: Vite
- **路由**: React Router v6
- **狀態管理**: React Context + Hooks
- **樣式**: CSS Variables + Tailwind CSS utilities

### 後端 (Backend)

- **框架**: FastAPI (Python 3.10)
- **認證**: JWT + Fernet 加密
- **資料庫**: PostgreSQL 16 (使用 RealDictCursor)
- **快取**: Redis (session 儲存)
- **向量資料庫**: ChromaDB

### AI/ML

- **語音辨識**: Qwen3-ASR-0.6B (本地運行)
- **LLM**: Ollama (qwen2.5:1.5b 本地模型)
- **Embedding**: qwen3-embedding:0.6b

## 資料庫架構

### PostgreSQL 資料表

#### main_menu (主餐菜單)

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 商品 ID |
| class | TEXT | 分類 (如：台式蛋餅) |
| name | TEXT | 名稱 (如：原味) |
| price | NUMERIC | 單價 |
| add_egg | BOOLEAN | 可加蛋 |
| cheese | BOOLEAN | 可加起司 |
| kimchi | BOOLEAN | 可加泡菜 |
| roast | BOOLEAN | 可加燒肉 |
| cheese_milk | BOOLEAN | 可某加起司牛奶 |
| danish | BOOLEAN | 可加丹麥 |
| combo | BOOLEAN | 是否為套餐 |
| vegetarian | BOOLEAN | 是否為素食 |
| recommended | BOOLEAN | 是否為推薦 |

#### drink_item (飲料菜單)

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 飲料 ID (字串如 1001) |
| class | TEXT | 分類 (如：特調飲品) |
| name | TEXT | 名稱 (如：古早紅茶) |
| M | NUMERIC | 中杯價格 |
| L | NUMERIC | 大杯價格 |

#### combo_menu (套餐菜單)

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 套餐 ID |
| name | TEXT | 套餐名稱 |
| price | NUMERIC | 套餐價格 |
| description | TEXT | 套餐描述 |

### Redis 資料結構

#### Session 訂單狀態

```
Key: {token_id}_order_state
Value: JSON object
{
  "order_id": "ORD202506151234",
  "order_time": "2025-06-15T10:30:00+08:00",
  "table_number": "",
  "customer": {"name": "", "phone": ""},
  "items": [
    {
      "id": "11015",
      "item_id": 1,
      "class": "台式蛋餅",
      "name": "原味",
      "unitPrice": 30.0,
      "subtotal": 50.0,
      "quantity": 2,
      "customization": {"cus_price": 20, "note": "加蛋、起司"}
    }
  ],
  "total_price": 100.0,
  "payment": {"method": "現金", "status": "unpaid"},
  "order_type": "",
  "status": "start"
}
```

#### 對話歷史

```
Key: {token_id}_conversation
Value: JSON array of conversation messages
```

## API 架構

### 路由模組

| 模組 | 前綴 | 檔案 |
|------|------|------|
| order | `/order` | blueprint/order.py |
| token | (無前綴) | blueprint/token.py |
| payment | (無前綴) | blueprint/payment.py |
| audioSSE | (無前綴) | blueprint/asr_stream.py |

### 認證流程

```
1. 用戶訪問前端 → 前端呼叫 /get-token
2. 後端產生 UUID token_id → 存入 Redis
3. 後端產生 JWT access_token → 用 Fernet 加密
4. 後端設定 HttpOnly Cookie → 返回前端
5. 後續請求自動攜帶 Cookie → 後端驗證
```

### 購物車流程

```
1. 用戶點擊「加入購物車」
2. 前端呼叫 POST /order/add-item
3. 後端驗證 token → 查詢商品資料
4. 更新 Redis 中的 order_state
5. 返回更新後的訂單狀態
```

## 前端路由架構

| 路徑 | 頁面 | 說明 |
|------|------|------|
| `/` | Home | 首頁，開始點餐 |
| `/menu` | Menu | 菜單瀏覽與選擇 |
| `/order` | VoiceOrder | 語音點餐 |
| `/orderview` | OrderView | 購物車/訂單檢視 |
| `/payment` | Payment | 結帳與付款 |

## 關鍵模組說明

### setup.py

後端初始化模組，負責：
- 載入環境變數
- 初始化 ChromaDB 向量資料庫
- 建立資料庫連線
- 初始化 Redis 客戶端

### rag/rag_morning_eat.py

RAG 點餐邏輯核心：
- `order_real_time()` - 處理即時語音點餐
- `create_prompt_template()` - 建立提示範本
- 使用向量搜尋增強生成

### blueprint/order.py

REST 購物車 API：
- `_verify_token()` - 驗證並取得 token_id
- `_get_item_from_db()` - 查詢商品
- `_add_item_to_order_state()` - 更新訂單狀態

### frontend/TokenContext.tsx

前端 Token 管理：
- 提供 `useToken` Hook
- 自動初始化與刷新 Token
- 管理全域載入狀態