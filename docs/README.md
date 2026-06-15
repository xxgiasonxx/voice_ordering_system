# 文件目錄

本資料夾包含晨式吃早餐語音點餐系統的完整技術文件。

## 文件列表

| 文件 | 說明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系統架構與技術詳細說明 |
| [API.md](API.md) | API 端點完整文件 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署指南 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 開發指南 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 常見問題與解決方案 |

## 快速參考

### 服務 URL

| 服務 | URL |
|------|------|
| 前端 | http://localhost |
| 後端 API | http://localhost:8000 |
| API 文件 | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Ollama | http://localhost:11434 |

### 預設憑證

| 服務 | 帳號 | 密碼 |
|------|------|------|
| PostgreSQL | postgres | postgres |
| Redis | (無密碼) | - |

### Docker 容器

| 容器名稱 | 服務 |
|----------|------|
| voice_ordering_system-frontend | 前端 |
| voice_ordering_system-backend | 後端 API |
| voice_ordering_system-postgres | 資料庫 |
| voice_ordering_system-redis | 快取 |
| voice_ordering_system-ollama | AI 模型服務 |