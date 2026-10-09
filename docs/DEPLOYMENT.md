# 部署指南

本系統使用 Docker Compose 部署，一個指令啟動全部服務。

## 環境需求

### 最低需求

- **CPU**：4 核心
- **記憶體**：8 GB RAM
- **磁碟**：約 10 GB 可用空間（映像檔 + 模型約 2 GB + 資料）
- **OS**：Windows 10/11（WSL2）、Linux 或 macOS
- **麥克風**：使用語音點餐的電腦需要麥克風。Mac mini 等沒有內建麥克風的機器，需接有麥克風的耳機或外接麥克風

### GPU（選用）

- **NVIDIA GPU**（Linux / Windows WSL2）：可讓 Ollama 使用 GPU，見下方[啟用 GPU 加速](#啟用-gpu-加速)
- **Mac**：Docker 無法使用 Apple GPU，Ollama 在容器裡只能用 CPU，每句回覆約 11–14 秒

## 快速部署

### 1. 確認環境

```bash
docker --version
docker compose version

# Windows：確認 WSL2
wsl --status
```

### 2. 啟動服務

```bash
git clone <repo-url>
cd voice_ordering_system

docker compose up -d --build
```

### 3. 第一次啟動會發生什麼

| 順序 | 服務 | 動作 | 時間 |
|------|------|------|------|
| 1 | postgres、redis | 啟動 | 數秒 |
| 2 | ollama | `ollama-entrypoint.sh` 下載 `qwen3:1.7b`、`qwen3-embedding:0.6b`（約 2 GB） | 視網速，數分鐘 |
| 3 | backend | **等 Ollama 兩個模型都下載完**才啟動（healthcheck，最多等 15 分鐘） | — |
| 4 | backend | 資料庫沒有菜單時，自動執行 `debug_and_migrate.py` 匯入 | 數秒 |
| 5 | backend | 從 Hugging Face 下載並預載 Moonshine 語音模型（約 100 MB） | 視網速 |

第二次之後啟動，模型和資料庫都已存在（保存在 volume），會快很多。

### 4. 驗證部署

```bash
docker compose ps                     # 所有服務應為 running / healthy
docker compose logs backend | tail    # 看到 "ASR model preloaded" 代表就緒

curl -I http://localhost              # 前端
curl http://localhost:8000/menu       # 後端 + 資料庫，應回傳菜單 JSON
curl http://localhost:11434/api/tags  # Ollama 模型清單
```

### 5. 開始使用

1. 開啟 http://localhost （從首頁進入；直接開啟子頁面網址會 404）
2. 選擇語音點餐 → 點「開始說話點餐」→ 允許麥克風權限
3. 按住麥克風按鈕說話，放開後等待回覆

## Docker 服務

### 服務列表

| 服務 | 連接埠 | 說明 |
|------|--------|------|
| frontend | 80 | React 前端（Nginx） |
| backend | 8000 | FastAPI 後端，含 Moonshine 語音辨識 |
| postgres | 5432 | 菜單資料庫 |
| redis | 6379 | 訂單與對話 session |
| ollama | 11434 | LLM 與 embedding 模型 |

### 持久化資料（volume）

| Volume | 內容 |
|------|------|
| `postgres_data` | 菜單資料庫 |
| `redis_data` | 訂單 session |
| `ollama_data` | Ollama 模型（約 2 GB） |

> ⚠️ `docker compose down -v` 會刪除以上所有 volume，下次啟動需重新下載模型、重新匯入菜單。平常停止請用 `docker compose down`。

Moonshine 語音模型的快取（`HF_HOME=/root/.cache/huggingface`）沒有掛 volume，重建後端容器後會重新下載（約 100 MB）。

## 啟用 GPU 加速

有 NVIDIA GPU 的機器（Linux / Windows WSL2，需安裝 NVIDIA Container Toolkit）加上 `docker-compose.gpu.yml`：

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Mac 沒有 NVIDIA GPU，直接用 `docker compose up -d`；若在 Mac 上加了 GPU 設定，會出現 `could not select device driver "nvidia"` 而無法啟動。

後端的語音辨識固定使用 CPU（模型很小，每句約 0.1–0.5 秒），GPU 只影響 Ollama。

## 生產環境配置

### 1. 更換密鑰

編輯 `docker-compose.yml`：

```yaml
environment:
  SECRET_KEY: "your-production-secret-key-here"   # 至少 32 字元
  FERNET_KEY: "your-production-fernet-key-here"
```

產生 Fernet 金鑰：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. 啟用 HTTPS

用反向代理（如 Nginx）處理 HTTPS。注意語音點餐使用 WebSocket，需要轉發 `Upgrade` header：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
    }

    location /asr {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;   # LLM 在 CPU 上回覆可能超過一分鐘
    }
}
```

> 前端目前把 WebSocket 位址寫死為 `ws://localhost:8000/asr`（`frontend/src/pages/VoiceOrder.tsx`），部署到其他網域時需一併修改。瀏覽器在非 `localhost` 的 HTTP 網頁上不允許使用麥克風，正式部署必須使用 HTTPS。

### 3. 調整 CORS

編輯 `backend/app.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 資料庫

### 自動初始化

後端每次啟動都會檢查 `main_menu`：不存在或沒有資料時，自動執行 `debug_and_migrate.py`（`morning_eat.xlsx` → SQLite → PostgreSQL）。已有資料則跳過。

### 手動重新匯入菜單

修改 `backend/morning_eat.xlsx` 後：

```bash
docker compose up -d --build backend                       # 把新的 xlsx 打包進映像
docker compose exec backend python debug_and_migrate.py    # 重新匯入（會清空並重建菜單資料表）
```

### 備份與還原

```bash
# 備份 PostgreSQL
docker compose exec postgres pg_dump -U postgres morning_eat > backup.sql

# 還原
cat backup.sql | docker compose exec -T postgres psql -U postgres morning_eat

# 備份 Redis
docker compose exec redis redis-cli BGSAVE
docker compose cp redis:/data/dump.rdb ./redis_backup.rdb
```

## 更新部署

```bash
git pull
docker compose up -d --build
docker image prune -f   # 清除舊映像
```

## 監控與日誌

```bash
docker compose logs -f backend
docker compose logs --tail=100 ollama
```

後端每句語音會印出：

```
ASR (2.4s, peak=0.596): '我要一份玉米蛋餅'     # 語音長度、音量峰值、辨識結果
LLM (11.2s): '好喔，台式蛋餅-玉米 40 元！...'   # LLM 花費時間與回覆
```

`peak` 接近 `0.000` 代表瀏覽器沒有收到麥克風聲音，見 [TROUBLESHOOTING.md](TROUBLESHOOTING.md#說話後沒有反應或回覆沒有收到聲音)。

## 卸載

```bash
docker compose down              # 停止服務（保留資料）
docker compose down -v           # 連同 volume 刪除（模型、資料庫都會清空）
docker compose down --rmi all    # 連同映像刪除
```

## 常見部署問題

1. **`could not select device driver "nvidia"`**：在沒有 NVIDIA GPU 的機器上用了 GPU 設定，改用 `docker compose up -d`
2. **後端一直沒啟動**：Ollama 還在下載模型，查看 `docker compose logs -f ollama`
3. **WSL2 記憶體不足**：在 `C:\Users\<username>\.wslconfig` 調整：
   ```ini
   [wsl2]
   memory=8GB
   swap=4GB
   ```
4. **連接埠衝突**：檢查 80、8000、5432、6379、11434 是否被佔用
   ```bash
   lsof -i :8000          # macOS / Linux
   netstat -ano | findstr :8000   # Windows
   ```
