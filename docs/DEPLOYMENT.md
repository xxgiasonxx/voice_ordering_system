# 部署指南

本系統使用 Docker Compose 進行容器化部署，支援快速啟動和水平擴展。

## 部署環境需求

### 最低需求

- **CPU**: 4 核心 (支援虛擬化)
- **記憶體**: 8 GB RAM
- **磁碟**: 20 GB 可用空間
- **OS**: Windows 10/11 (WSL2) 或 Linux/macOS

### 建議規格

- **CPU**: 8+ 核心 (AI 模型需要 GPU 加速)
- **記憶體**: 16+ GB RAM
- **GPU**: NVIDIA GPU (4+ GB VRAM) - 用於本地 AI 模型

## 快速部署

### 1. 確認環境

```bash
# 確認 Docker 已安裝
docker --version
docker compose version

# 確認 WSL2 (Windows)
wsl --status
```

### 2. 啟動服務

```bash
# 複製專案
git clone <repo-url>
cd voice_ordering_system

# 啟動所有服務 (首次啟動會下載模型，約 5-10 分鐘)
docker compose up -d

# 查看服務狀態
docker compose ps
```

### 3. 驗證部署

```bash
# 檢查服務健康狀態
docker compose ps

# 測試前端
curl -I http://localhost

# 測試後端 API
curl http://localhost:8000/menu

# 查看 API 文件
open http://localhost:8000/docs
```

### 4. 首次使用

1. 開啟瀏覽器訪問 http://localhost
2. 點擊「開始點餐」進入語音或選單模式
3. 允許麥克風權限 (語音模式)
4. 開始點餐

## Docker 服務說明

### 服務架構

| 服務 | 連接埠 | 說明 |
|------|--------|------|
| frontend | 80 | React 前端靜態網頁 |
| backend | 8000 | FastAPI 後端 API |
| postgres | 5432 | PostgreSQL 資料庫 |
| redis | 6379 | Redis 快取伺服器 |
| ollama | 11434 | Ollama AI 模型服務 |

### 持久化資料

```yaml
volumes:
  postgres_data:/var/lib/postgresql/data  # 資料庫資料
  redis_data:/data                         # Redis 資料
  ollama_data:/root/.ollama               # AI 模型
```

## 生產環境配置

### 1. 更新秘密金鑰

編輯 `docker-compose.yml`，更換以下環境變數：

```yaml
environment:
  SECRET_KEY: "your-production-secret-key-here"      # 至少 32 字元
  FERNET_KEY: "your-production-fernet-key-here"      # 使用 openssl 生成
```

生成 Fernet 金鑰：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. 啟用 HTTPS

生產環境建議使用反向代理 (如 Nginx) 處理 HTTPS：

```nginx
# Nginx 配置範例
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### 3. 調整 CORS 設定

編輯 `backend/app.py` 中的 CORS 白名單：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 效能優化

#### 後端 replicas
```bash
docker compose up -d --scale backend=3
```

#### 啟用 GPU 加速
```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## 資料庫遷移

### 初始化資料庫

```bash
# 執行遷移腳本
docker compose exec backend python debug_and_migrate.py
```

### 手動備份資料庫

```bash
# 備份 PostgreSQL
docker compose exec postgres pg_dump -U postgres morning_eat > backup.sql

# 還原
cat backup.sql | docker compose exec -T postgres psql -U postgres morning_eat
```

### 備份 Redis Session

```bash
# 備份 Redis
docker compose exec redis redis-cli BGSAVE
docker compose cp redis:/data/dump.rdb ./redis_backup.rdb
```

## 更新部署

```bash
# 拉取最新程式碼
git pull

# 重新建構並啟動
docker compose up -d --build

# 清除舊容器
docker container prune -f
```

## 監控與日誌

### 查看日誌

```bash
# 所有服務
docker compose logs -f

# 特定服務
docker compose logs -f backend
docker compose logs -f frontend

# 最近 100 行
docker compose logs --tail=100 backend
```

### 健康檢查

```bash
# 檢查容器狀態
docker compose ps

# 手動健康檢查
curl -f http://localhost:8000/me
curl -f http://localhost:8000/menu
```

## 卸載

```bash
# 停止服務
docker compose down

# 刪除資料卷 (慎用！會刪除所有資料)
docker compose down -v

# 刪除所有容器和映像
docker compose down --rmi all
```

## 故障排除

### 常見部署問題

1. **WSL2 記憶體不足**
   ```powershell
   # C:\Users\<username>\.wslconfig
   wslconfig /setmemory 8192
   wslconfig /setswap 4096
   ```

2. **連接埠衝突**
   ```bash
   # 檢查佔用
   netstat -ano | findstr :80
   netstat -ano | findstr :8000
   ```

3. **容器無法啟動**
   ```bash
   # 查看詳細錯誤
   docker compose logs <service-name>

   # 重建特定服務
   docker compose up -d --build --no-cache <service-name>
   ```