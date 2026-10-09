# 故障排除

本文件收錄常見問題與解決方案。

## 快速診斷

```bash
docker compose ps                          # 容器狀態
docker compose logs backend --tail=50      # 後端日誌
curl http://localhost:8000/menu            # 後端 + 資料庫
curl http://localhost:11434/api/tags       # Ollama 模型是否下載完成
```

語音點餐時，後端每句會印出一行 ASR 與 LLM 的紀錄，是判斷問題出在哪一段的最快方式：

```
ASR (2.4s, peak=0.596): '我要一份玉米蛋餅'      ← 語音長度、音量峰值、辨識結果
LLM (11.2s): '好喔，台式蛋餅-玉米 40 元！...'    ← LLM 花費時間與回覆
```

| 看到的狀況 | 跳到 |
|------|------|
| 沒有任何 `ASR (...)` 紀錄 | [語音送不到後端](#語音送不到後端) |
| `peak=0.000`、辨識結果 `''` | [說話後沒有反應，或回覆「沒有收到聲音」](#說話後沒有反應或回覆沒有收到聲音) |
| 回覆「不好意思，系統出了點問題」 | [LLM 步驟失敗](#llm-步驟失敗回覆系統出了點問題) |
| LLM 要等很久 | [回覆太慢](#回覆太慢) |

---

## 說話後沒有反應，或回覆「沒有收到聲音」

### 徵狀

後端 log 出現 `ASR (..., peak=0.000): ''`，前端回覆「沒有收到聲音耶，請確認麥克風有開、瀏覽器有麥克風權限喔！」。

### 原因

`peak` 是音量峰值（0～1）。真實麥克風即使沒人說話也會有一點底噪，**`0.000` 代表瀏覽器拿到的是完全無聲的音訊**，問題在麥克風而不是程式。

### 解決方案

1. **macOS 的麥克風權限**（最常見）
   - Chrome 網址列的「允許麥克風」只是網站權限；macOS 另外還有一層 App 權限
   - 系統設定 → 隱私權與安全性 → 麥克風 → 打開你使用的瀏覽器（已打開的話可以關掉再打開）
   - **按 ⌘Q 完全結束瀏覽器再重開**，只重新整理頁面不會生效
2. **電腦沒有可用的麥克風**
   - Mac mini 沒有內建麥克風，系統的「外接麥克風」是耳機孔；插一般只能聽的耳機時錄不到人聲
   - 改用有麥克風的耳機、USB 或藍牙麥克風
3. **瀏覽器選錯麥克風**：網址列左側圖示 → 麥克風 → 選擇正確的裝置

### 自我檢查

在瀏覽器打開 http://localhost，按 `⌘⌥J`（Windows：`Ctrl+Shift+J`）開啟主控台，貼上後按 Enter，**馬上對麥克風說話 3 秒**：

```js
(async()=>{const s=await navigator.mediaDevices.getUserMedia({audio:true});const t=s.getAudioTracks()[0];console.log('裝置:',t.label,'muted:',t.muted);const c=new AudioContext();const a=c.createAnalyser();c.createMediaStreamSource(s).connect(a);const d=new Float32Array(a.fftSize);let p=0;const end=Date.now()+3000;while(Date.now()<end){a.getFloatTimeDomainData(d);for(const v of d)p=Math.max(p,Math.abs(v));await new Promise(r=>setTimeout(r,50));}console.log('最大音量 peak =',p.toFixed(4));s.getTracks().forEach(x=>x.stop());c.close();})()
```

| 結果 | 代表 |
|------|------|
| `peak ≈ 0.0000` | 瀏覽器拿不到麥克風 → 檢查第 1 點 |
| `peak` 很小（0.01–0.05），說話也不變大 | 麥克風有通但收不到人聲 → 檢查第 2、3 點 |
| `peak > 0.1` | 麥克風正常；若點餐頁仍是 `peak=0.000`，請回報問題 |

### peak 正常但辨識結果是空的

太小聲或只有雜音時，語音辨識會回傳空字串，前端回覆「沒聽清楚」。不到 0.33 秒的語音會被當成誤觸，直接忽略、不會回覆。請按住按鈕、說完整句再放開。

---

## 語音送不到後端

### 徵狀

按住按鈕說話、放開後沒有任何回覆，後端 log 也沒有 `ASR (...)`。

### 解決方案

1. 確認按鈕是**按住說話、放開送出**，不是點一下
2. 頁面上方應顯示「麥克風就緒，按住按鈕說話」；若顯示「開始連線」，點它重新連線
3. 確認後端運作：`curl http://localhost:8000/menu`
4. 開發者工具 → Network → WS，確認 `ws://localhost:8000/asr` 已連線
5. 前端是舊版（沒有在放開按鈕時送出 `end_utterance`）時，重建前端：
   ```bash
   docker compose up -d --build frontend
   ```

---

## LLM 步驟失敗（回覆「系統出了點問題」）

### 徵狀

辨識結果正確，但回覆「不好意思，系統出了點問題，可以再說一次你的需求嗎？」。

### 解決方案

查看後端 log 中 `Ollama 推理失敗：` 後面的實際錯誤：

| 錯誤訊息 | 原因與處理 |
|------|------|
| `relation "main_menu" does not exist` | 資料庫沒有菜單。後端啟動時會自動匯入，重啟後端即可：`docker compose restart backend`；或手動執行 `docker compose exec backend python debug_and_migrate.py` |
| `model "qwen3:1.7b" not found` / `model "qwen3-embedding:0.6b" not found` | Ollama 模型還沒下載完或被刪除，見[模型找不到](#模型找不到) |
| `Connection refused`（連 ollama） | Ollama 容器沒有運作：`docker compose ps ollama` |

---

## 模型找不到

### 徵狀

`model "..." not found, try pulling it first`。

### 解決方案

```bash
docker compose logs ollama --tail=50                       # 確認是否還在下載
docker compose exec ollama ollama list                     # 已下載的模型
docker compose exec ollama ollama pull qwen3:1.7b          # 手動下載
docker compose exec ollama ollama pull qwen3-embedding:0.6b
```

語音辨識模型（Moonshine）不在 Ollama，而是後端從 Hugging Face 下載，log 會顯示 `Loading Moonshine ASR model`。

### 每次啟動都要重新下載模型

停止服務時用了 `docker compose down -v`，`-v` 會刪除存放模型的 volume。平常請用 `docker compose down`。

---

## 回覆太慢

### 原因

時間幾乎都花在 LLM。Mac 上的 Docker 無法使用 GPU，Ollama 只能用 CPU：

| 環境 | 每句回覆 |
|------|------|
| Mac + Docker（CPU） | 約 11–14 秒；模型剛載入的第一句約 60 秒 |
| Mac 原生 Ollama（Apple GPU） | 約 6 秒 |
| NVIDIA GPU（`docker-compose.gpu.yml`） | 視顯卡而定 |

### 解決方案

- 有 NVIDIA GPU：`docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`
- 第一句特別慢是載入模型，之後會維持在記憶體中（`OLLAMA_KEEP_ALIVE=24h`）
- 不建議換更小的模型：實測 `qwen3:0.6b`、`qwen3.5:0.8b` 在 CPU 上只快 2–4 秒，但準確率從 26–27/27 降到 20–21/27

---

## 後端一直沒有啟動

### 原因

後端會等 Ollama 的兩個模型下載完成才啟動（Ollama healthcheck，最多等 15 分鐘）。

### 解決方案

```bash
docker compose ps                    # ollama 應從 starting 變成 healthy
docker compose logs -f ollama        # 查看下載進度
```

下載超過 15 分鐘 healthcheck 會判定失敗，後端不會啟動。網路很慢時可在 `docker-compose.yml` 調大 ollama 的 `start_period`，或下載完成後再執行一次 `docker compose up -d`。

---

## 服務無法啟動

### `could not select device driver "nvidia" with capabilities: [[gpu]]`

在沒有 NVIDIA GPU 的機器（例如 Mac）上使用了 GPU 設定。直接用 `docker compose up -d`，不要加 `docker-compose.gpu.yml`。

### 其他錯誤

```bash
docker compose logs <service-name>         # 查看錯誤
docker compose up -d --build <service-name>
```

**連接埠被佔用**（80、8000、5432、6379、11434）：
```bash
lsof -i :8000                    # macOS / Linux
netstat -ano | findstr :8000     # Windows
```

**磁碟空間不足**：
```bash
docker system df
docker image prune -f
```

> 清理時避免使用 `docker volume prune` 或 `docker compose down -v`，會刪除模型與資料庫。

---

## 開啟子頁面顯示 404

### 徵狀

直接開啟 `http://localhost/voiceorder` 等網址，或在子頁面重新整理，出現 404。

### 原因

前端 Nginx 沒有設定前端路由回退（`try_files $uri /index.html`）。

### 解決方案

從 http://localhost 首頁進入，用頁面上的按鈕切換。

---

## 前端顯示「網路錯誤」

### 解決方案

```bash
curl http://localhost:8000/menu                 # 1. 確認後端運作
docker compose up -d --build frontend           # 2. 重建前端
```

3. 清除瀏覽器 Cookie 與快取後重新整理
4. 確認 `docker-compose.yml` 中的前端環境變數：
   ```yaml
   VITE_BACKEND_API_URL: http://localhost:8000
   VITE_API_BASE_URL: http://localhost:8000
   ```

---

## CORS 錯誤

### 徵狀

```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

### 解決方案

在 `backend/app.py` 的 `allow_origins` 加上前端網址（例如 Vite 開發伺服器的 `http://localhost:5173`），`allow_credentials` 必須為 `True`，然後重建後端：

```bash
docker compose up -d --build backend
```

---

## 購物車為空

### 原因

1. Cookie（`ordering_token`）沒有正確帶上
2. Redis 資料過期或被清除

### 解決方案

```bash
curl -v http://localhost:8000/see_order                    # 測試 API
docker compose exec redis redis-cli KEYS "*_order_state"   # 檢查 Redis
```

清除瀏覽器 Cookie 後重新整理，會重新建立 session。

---

## 飲料價格顯示錯誤或語音點飲料失敗

### 原因

PostgreSQL 的 `drink_item` 欄位被建成小寫 `m` / `l`（舊版遷移腳本沒有加引號），而程式讀取大寫的 `M` / `L`。

### 解決方案

用新版腳本重新匯入（會重建資料表）：

```bash
docker compose up -d --build backend
docker compose exec backend python debug_and_migrate.py
```

---

## Redis 連線錯誤

### 徵狀

`ConnectionError: Error -2 connecting to redis`。

### 解決方案

```bash
docker compose ps redis
docker compose exec redis redis-cli ping
docker compose restart redis backend
```

---

## Token 過期

API 回傳 401，重新整理後又正常：這是預期行為。過期時間由 `docker-compose.yml` 的 `TOKEN_EXPIRE_MINUTES` 設定（預設 300 分鐘）。

---

## 資料備份

PostgreSQL 只存菜單，可隨時從 `backend/morning_eat.xlsx` 重新匯入；訂單與對話紀錄存在 Redis。

```bash
# 備份 Redis（訂單）
docker compose exec redis redis-cli BGSAVE
docker compose cp redis:/data/dump.rdb ./redis_backup.rdb

# 備份 PostgreSQL（菜單）
docker compose exec postgres pg_dump -U postgres morning_eat > backup_$(date +%Y%m%d).sql
cat backup_20250615.sql | docker compose exec -T postgres psql -U postgres morning_eat   # 還原
```

---

## 獲取更多幫助

```bash
docker compose logs > debug.log 2>&1    # 完整日誌
docker stats                            # 資源使用
```
