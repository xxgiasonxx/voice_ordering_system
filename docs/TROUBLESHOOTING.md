# 故障排除

本文件收錄常見問題與解決方案。

## 快速診斷

執行以下命令快速檢查系統狀態：

```bash
# 1. 檢查容器狀態
docker compose ps

# 2. 檢查後端日誌
docker compose logs backend --tail=50

# 3. 測試 API
curl http://localhost:8000/menu
```

---

## 服務無法啟動

### 徵狀

Docker 容器無法啟動或立即停止。

### 解決方案

```bash
# 1. 查看詳細錯誤
docker compose logs <service-name>

# 2. 移除並重新建立
docker compose down
docker compose up -d

# 3. 清除 Docker 緩存後重試
docker system prune -a
docker compose up -d --build
```

### 常見錯誤

**連接埠被佔用**
```bash
# 找出佔用行程
netstat -ano | findstr :8000
netstat -ano | findstr :80

# 終止行程或修改 docker-compose.yml 中的連接埠映射
```

**磁碟空間不足**
```bash
# 檢查磁碟使用
docker system df

# 清理未使用的資源
docker system prune -f
docker volume prune -f
```

---

## 前端顯示「網路錯誤」

### 徵狀

瀏覽器出現「Error: Network Error」或無法載入資料。

### 原因

1. CORS 設定不正確
2. 後端 API 未運行
3. Cookie 未正確設定

### 解決方案

```bash
# 1. 確認後端運行
curl http://localhost:8000/menu

# 2. 清除瀏覽器 Cookie 和快取
# Ctrl+Shift+Del → 清除瀏覽資料

# 3. 確認前端環境變數
# docker-compose.yml 中:
VITE_BACKEND_API_URL: http://localhost:8000
VITE_API_BASE_URL: http://localhost:8000

# 4. 重建前端
docker compose up -d --build frontend
```

---

## 購物車為空

### 徵狀

加入商品後，購物車頁面顯示空或顯示舊資料。

### 原因

1. Token 未正確傳遞
2. Redis 資料未正確儲存
3. API 路徑錯誤 (使用 `/payment/see_order` 而非 `/see_order`)

### 解決方案

```bash
# 1. 確認前端 API 路徑正確
# 應該是 /see_order 不是 /payment/see_order

# 2. 清除瀏覽器 Cookie 並重新整理

# 3. 檢查 Redis 中的資料
docker compose exec redis redis-cli GET "*_order_state"

# 4. 測試 API
curl -v http://localhost:8000/see_order
```

---

## 語音辨識無回應

### 徵狀

點擊麥克風按鈕後沒有反應，或無法錄音。

### 原因

1. 麥克風權限未授權
2. Ollama 或 ASR 模型未正確載入
3. 瀏覽器不支援 Web Audio API

### 解決方案

```bash
# 1. 確認 Ollama 服務運行
curl http://localhost:11434/api/version

# 2. 確認 ASR 模型已下載
docker compose exec ollama ollama list

# 3. 檢查後端日誌
docker compose logs backend --tail=100 | grep -i asr

# 4. 確認前端無錯誤
# 開啟瀏覽器開發者工具 → Console
```

### 瀏覽器設定

```
Chrome: 設定 → 隱私權 → 網站設定 → 麥克風 → 允許 localhost
Firefox: 選項 → 隱私權與安全性 → 麥克風 → 允許
```

---

## 資料庫連線錯誤

### 徵狀

`psql: error: connection to server failed` 或 `could not connect to database`

### 原因

1. PostgreSQL 未運行
2. 連線憑證錯誤
3. 資料庫不存在

### 解決方案

```bash
# 1. 確認 PostgreSQL 運行
docker compose ps postgres

# 2. 檢查健康狀態
docker compose inspect postgres | grep -i health

# 3. 等待資料庫就緒後重試
docker compose up -d postgres
sleep 10

# 4. 手動建立資料庫 (如需要)
docker compose exec postgres psql -U postgres -c "CREATE DATABASE morning_eat;"

# 5. 執行遷移
docker compose exec backend python debug_and_migrate.py
```

---

## Redis 連線錯誤

### 徵狀

`ConnectionError: Error -2 connecting to redis` 或類似錯誤。

### 解決方案

```bash
# 1. 確認 Redis 運行
docker compose ps redis

# 2. 測試連線
docker compose exec redis redis-cli ping

# 3. 從後端容器測試
docker compose exec backend python -c "from setup import redis_client; print(redis_client.ping())"

# 4. 重啟 Redis
docker compose restart redis
```

---

## AI 模型載入失敗

### 徵狀

後端日誌顯示 `Failed to initialize embedding model` 或 ASR 模型載入失敗。

### 解決方案

```bash
# 1. 確認 Ollama 容器運行
docker compose ps ollama

# 2. 檢查 Ollama 日誌
docker compose logs ollama --tail=50

# 3. 手動下載模型
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose exec ollama ollama pull qwen3-embedding:0.6b
docker compose exec ollama ollama pull qwen3-asr:0.6b

# 4. 重啟後端
docker compose restart backend
```

---

## CORS 錯誤

### 徵狀

瀏覽器主控台顯示：
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost' 
has been blocked by CORS policy
```

### 原因

後端 CORS 設定不允許前端網域。

### 解決方案

編輯 `backend/app.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:5173",  # Vite 開發伺服器
    ],
    allow_credentials=True,  # 必須為 True
    allow_methods=["*"],
    allow_headers=["*"],
)
```

然後重建後端：
```bash
docker compose up -d --build backend
```

---

## Token 過期

### 徵狀

API 請求返回 401 Unauthorized，但重新整理頁面後又正常。

### 解決方案

這是預期行為。Token 過期後，系統會自動引導用戶重新開始。

如需調整過期時間，修改 `docker-compose.yml`：
```yaml
environment:
  TOKEN_EXPIRE_MINUTES: 300  # 預設 300 分鐘 (5 小時)
```

---

## 資料遺失

### 徵狀

重啟 Docker 後訂單資料或自訂資料消失。

### 原因

未使用持久化 volume 或 volume 意外刪除。

### 解決方案

```bash
# 檢查 volume 狀態
docker volume ls | grep voice_ordering

# 重建 volume (慎用！會刪除資料)
docker compose down -v
docker compose up -d
```

### 建議

定期備份資料庫：
```bash
# 備份
docker compose exec postgres pg_dump -U postgres morning_eat > backup_$(date +%Y%m%d).sql

# 還原
cat backup_20250615.sql | docker compose exec -T postgres psql -U postgres morning_eat
```

---

## 效能問題

### 前端載入緩慢

```bash
# 1. 檢查網路
curl -I http://localhost

# 2. 清理瀏覽器快取

# 3. 重建前端
docker compose up -d --build frontend
```

### API 回應緩慢

```bash
# 1. 檢查後端資源使用
docker stats

# 2. 檢查資料庫查詢效能
docker compose exec postgres psql -U postgres -d morning_eat -c "SELECT * FROM pg_stat_activity;"

# 3. 檢查 Redis 快取
docker compose exec redis redis-cli INFO stats
```

---

## 獲取更多幫助

1. **查看完整日誌**
   ```bash
   docker compose logs -f > debug.log 2>&1
   ```

2. **檢查系統資源**
   ```bash
   docker stats
   free -h
   df -h
   ```

3. **重置所有服務**
   ```bash
   docker compose down
   docker system prune -f
   docker compose up -d
   ```