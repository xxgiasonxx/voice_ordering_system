# 文件目錄

本資料夾包含晨式吃早餐語音點餐系統的完整技術文件。

## 文件列表

| 文件 | 說明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系統架構、語音點餐流程、資料庫結構 |
| [API.md](API.md) | REST API 與 WebSocket `/asr` 訊息格式 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署、首次啟動流程、GPU、備份 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 本機開發、修改點餐邏輯與菜單 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 常見問題（麥克風沒聲音、回覆慢、模型找不到…） |

快速開始請看專案根目錄的 [README](../README.md)。

## 快速參考

### 服務 URL

| 服務 | URL |
|------|------|
| 前端 | http://localhost |
| 後端 API | http://localhost:8000 |
| API 文件 | http://localhost:8000/docs |
| 語音點餐 WebSocket | ws://localhost:8000/asr |
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
| voice_ordering_system-backend | 後端 API（含 Moonshine 語音辨識） |
| voice_ordering_system-postgres | 資料庫 |
| voice_ordering_system-redis | 快取 |
| voice_ordering_system-ollama | LLM 與 embedding 模型（qwen3:1.7b、qwen3-embedding:0.6b） |