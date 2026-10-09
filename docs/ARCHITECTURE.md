# 系統架構

## 整體架構圖

```
┌──────────────────────────────────────────────────────────────────┐
│                         瀏覽器 http://localhost                    │
│     REST (購物車/菜單/付款)          WebSocket /asr (語音點餐)      │
└──────────────┬───────────────────────────────┬───────────────────┘
               ▼                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Docker Network                                                   │
│  ┌────────────┐   ┌───────────────────────────┐   ┌───────────┐  │
│  │  Frontend  │   │         Backend           │──►│   Redis   │  │
│  │  Nginx :80 │   │      FastAPI :8000        │   │   :6379   │  │
│  └────────────┘   │  ・Moonshine 語音辨識(CPU) │   │ 訂單/對話  │  │
│                   │  ・品項比對、prompt、解析   │   └───────────┘  │
│                   │  ・ChromaDB 菜單檢索       │   ┌───────────┐  │
│                   │                           │──►│ PostgreSQL│  │
│                   └─────────────┬─────────────┘   │   :5432   │  │
│                                 ▼                 │   菜單     │  │
│                   ┌───────────────────────────┐   └───────────┘  │
│                   │     Ollama :11434         │                  │
│                   │  qwen3:1.7b (LLM)         │                  │
│                   │  qwen3-embedding:0.6b     │                  │
│                   └───────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

語音辨識在後端容器內執行（transformers，CPU），不經過 Ollama。Ollama 只負責 LLM 與 embedding。

## 技術棧

### 前端

- React + TypeScript、Vite 建構、Nginx 提供靜態檔
- React Router、React Context（Token 管理）
- 錄音：Web Audio API（`AudioContext` 16kHz + `ScriptProcessorNode`），轉成 16-bit PCM 經 WebSocket 傳送

### 後端

- FastAPI (Python 3.10)
- 認證：JWT + Fernet 加密的 HttpOnly Cookie
- PostgreSQL 16（`RealDictCursor`、autocommit）；未設定 `DB_URL` 時改用 SQLite
- Redis：訂單與對話 session
- ChromaDB：菜單向量檢索

### AI 模型

| 用途 | 模型 | 執行位置 |
|------|------|------|
| 語音辨識 | `moonshine-ai/moonshine-streaming-tiny-zh`（27M 參數） | 後端容器，CPU 版 PyTorch |
| LLM | `qwen3:1.7b`（`reasoning=False` 關閉思考模式、`temperature=0.1`） | Ollama |
| Embedding | `qwen3-embedding:0.6b` | Ollama |
| 簡轉繁 | OpenCC `s2tw`（並把「臺」改回「台」） | 後端 |
| 拼音比對 | pypinyin | 後端 |

## 語音點餐流程

### 1. 錄音（前端 `pages/VoiceOrder.tsx`）

- 按住按鈕時，每 4096 個取樣（16kHz 下約 256ms）送出一段 16-bit PCM
- 放開按鈕時送出文字訊息 `{"type": "end_utterance"}`，告訴後端這句話說完了

### 2. 語音辨識（`blueprint/asr_stream.py`）

- 收到的音訊累積在 buffer；每多 2 秒就對目前整段辨識一次，回傳 `asr_partial` 當即時字幕（只顯示，不呼叫 LLM）
- 收到 `end_utterance` 後**整段辨識一次**，送出 `asr_final` 與 `cus`，再呼叫 LLM **一次**
- 辨識結果經 OpenCC 轉成台灣繁體
- 音訊不到 0.33 秒視為誤觸；單句最長保留 30 秒
- 辨識與 LLM 都丟到背景 thread 執行，不會卡住 WebSocket
- log 會印出 `ASR (秒數, peak=音量峰值): '辨識結果'`；peak 接近 0 代表瀏覽器沒收到聲音

### 3. 點餐理解（`rag/rag_morning_eat.py`）

1. **檢索**：ChromaDB 取出與這句話最相關的 10 筆菜單
2. **品項比對** `find_mentioned_items()`：直接比對顧客原話中提到的品項
   - 字面或拼音其中一個對上就算（「活推吐司」與「火腿吐司」拼音相同）
   - 同名品項（例如 台式蛋餅-火腿 / 吐司-火腿）要連類別一起提到才算
   - 名稱唯一的品項（例如 薯條、豆漿）只要提到名稱就算
3. **LLM**：prompt 包含指示、目前訂單、對話紀錄、檢索結果與比對到的品項，要求輸出兩個區塊：

   ````
   ```sys
   intent: order
   + 吐司-火腿 1 起司
   + 特調飲品-古早奶茶 1 大杯
   ```
   ```cus
   好喔，吐司-火腿加起司 40 元，古早奶茶大杯 35 元！還要啥？
   ```
   ````

4. **解析** `parse_llm_response()`：
   - 先把 LLM 輸出轉成繁體（小模型偶爾會輸出簡體）
   - `resolve_item()` 把「類別-品項名稱」對應回資料庫品項：完全比對 → 類別錯但品名唯一 → 模糊比對（相似度 ≥ 0.6）
   - LLM 選到同名但不同類別的品項時，以步驟 2 的比對結果為準
   - 價格、加料費用一律由程式依資料庫計算

**設計原因**：小模型很不擅長從大量菜單中挑出正確的數字 ID，但擅長照抄名稱。所以 LLM 只負責理解語意，ID 與價格交給程式。

### 4. 更新訂單（`blueprint/asr_stream.py` → `call_llm()`）

更新 Redis 中的訂單與對話紀錄，回傳 `llm`、`order` 訊息；若意圖為 `end` 則送出 `end` 並關閉連線。

WebSocket 訊息格式詳見 [API.md](API.md#websocket-asr)。

## 資料庫架構

### PostgreSQL 資料表

後端啟動時若 `main_menu` 不存在或是空的，`app.py` 會自動執行 `debug_and_migrate.py` 從 `morning_eat.xlsx` 匯入。

#### main_menu（主餐）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 品項 ID |
| class | TEXT | 類別（如：台式蛋餅） |
| name | TEXT | 名稱（如：原味） |
| price | REAL | 單價 |
| add_egg / cheese / kimchi / roast / cheese_milk / danish | INTEGER | 可否加蛋、起司、泡菜、燒肉、起司牛奶、山型丹麥（1=可、0=不可） |
| combo | TEXT | 可搭配的套餐（`A/B/C/D` 或 `無`） |
| vegetarian | INTEGER | 素食（1/0） |
| recommended | INTEGER | 推薦品項（1/0） |

#### drink_item（飲料）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 飲料 ID（如 `1001`） |
| class | TEXT | 類別（`特調飲品`） |
| name | TEXT | 名稱（如：古早紅茶） |
| "M" | REAL | 中杯價格 |
| "L" | REAL | 大杯價格（可為空） |

> `M`、`L` 建表與查詢時都要加雙引號。PostgreSQL 會把沒加引號的欄位名稱轉成小寫，而後端與前端都讀取大寫的 `M` / `L`。

#### combo_menu（套餐）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 套餐 ID（如 `A1`） |
| name | TEXT | 套餐名稱（`A`～`D`） |
| price | REAL | 加價 |
| description | TEXT | 內容（如：晨間薯餅+中杯紅茶(古早)） |

### Redis 資料結構

#### 訂單狀態

```
Key: {token_id}_order_state
Value: JSON
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

#### 對話紀錄

```
Key: {token_id}_conversation
Value: JSON array，元素為 {"type": "cus" | "llm" | "end", ...}
```

## API 架構

### 路由模組

| 模組 | 前綴 | 檔案 |
|------|------|------|
| order | `/order` | blueprint/order.py |
| token | （無） | blueprint/token.py |
| payment | （無） | blueprint/payment.py |
| audioSSE | （無） | blueprint/asr_stream.py（`/asr`、`/history`） |

### 認證流程

```
1. 前端呼叫 /get-token
2. 後端產生 UUID token_id → 在 Redis 建立訂單與對話紀錄
3. 產生 JWT → Fernet 加密 → 設為 HttpOnly Cookie (ordering_token)
4. 之後的 REST 請求與 WebSocket 連線都自動帶 Cookie，後端解密驗證
```

### 購物車流程

```
1. 使用者點「加入購物車」→ 前端呼叫 POST /order/add-item
2. 後端驗證 token → 查詢品項
3. 更新 Redis 中的 order_state → 回傳更新後的訂單
```

## 前端路由

| 路徑 | 頁面 | 說明 |
|------|------|------|
| `/` | Home | 首頁 |
| `/choice` | Choice | 選擇語音點餐或菜單點餐 |
| `/menu` | Menu | 菜單點餐 |
| `/voiceorder` | VoiceOrder | 語音點餐 |
| `/orderstate` | OrderState | 訂單狀態 |
| `/orderview` | OrderView | 購物車 / 訂單檢視 |
| `/payment` | Payment | 結帳與付款 |

> Nginx 目前沒有設定路由回退（`try_files ... /index.html`），直接開啟子頁面網址會 404，需從首頁進入。

## 啟動順序

```
postgres (healthy) ──┐
                     ├──► backend ──► 自動匯入菜單（若資料庫為空）──► 預載 Moonshine
ollama   (healthy) ──┘
```

- 後端沒有設定等待 Redis（`depends_on` 不含 redis）；Redis 通常啟動很快，但若後端啟動時 Redis 還沒就緒，`setup.py` 會連線失敗
- Ollama 的 healthcheck 要求 `qwen3:1.7b` 與 `qwen3-embedding:0.6b` 都下載完才算健康（`start_period: 15m`），避免後端在模型下載完成前就收到點餐請求
- 模型由 `ollama-entrypoint.sh` 在 Ollama 啟動時自動下載

## 關鍵模組

### setup.py

後端初始化：載入環境變數、初始化 embedding 與 ChromaDB、建立共用的資料庫連線、Redis 客戶端。

### rag/rag_morning_eat.py

點餐核心：
- `rag_query()` / `order_real_time()`：檢索 → 品項比對 → LLM → 解析
- `find_mentioned_items()`：從原話比對品項（字面 + 拼音）
- `resolve_item()`：LLM 輸出的品項名稱 → 資料庫品項
- `parse_llm_response()`：解析 `sys` / `cus` 區塊並更新訂單
- `create_prompt_template()`：prompt

### rag/useModel.py

依 `LLM_MODEL` 建立 LLM：`gemini_api` 使用 Gemini，其他名稱一律視為 Ollama 模型（`num_ctx=8192`、`num_predict=300`、`reasoning=False`、`temperature=0.1`）。

### blueprint/asr_stream.py

WebSocket `/asr`：累積音訊、即時字幕、整句辨識、呼叫 LLM、更新 Redis。

### frontend/src/contexts/TokenContext.tsx

前端 Token 管理：提供 `useToken`，自動初始化 session。
