# 語音點餐系統

## 介紹
本系統提供透過語音即時點餐的功能，無需繁瑣操作APP，直接以語音與大型語言模型（LLM）互動，提升點餐效率。

## 功能特色
- 語音辨識即時點餐
- 與LLM整合，智慧推薦餐點
- 前後端分離架構，易於維護與擴充

## 待改善
- 目前只支持中文
- 語音辨識不夠準確
- LLM回答不夠完美
- 介面不夠完善

## 安裝說明

### 環境需求
- Python 3.10.18
- Node.js 22.14.0
- npm 10.9.2
- Docker & Docker Compose（可選）

### 快速啟動

#### 使用 Docker
```bash
docker compose up -d
```

#### 本地開發

##### Backend
1. 安裝依賴（推薦使用 [uv](https://github.com/astral-sh/uv)）
    ```bash
    uv sync
    ```
2. 啟動後端服務
    ```bash
    uv run app.py
    ```
3. 或使用 Conda
    ```bash
    conda install -r requirements.txt
    ```

##### Frontend
1. 安裝依賴
    ```bash
    npm install
    ```
2. 啟動前端開發伺服器
    ```bash
    npm run dev
    ```

## 目錄結構
```
backend/
  app.py
  requirements.txt
frontend/
  ...
docker-compose.yml
README.md
```

## 聯絡方式
如有問題請聯絡專案維護者。