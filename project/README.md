語音點餐系統使用說明書

## 1. 系統概述

本語音點餐系統旨在為餐廳提供一個智能化的點餐解決方案，透過語音辨識和自然語言處理（NLP）技術，讓客戶能以自然語言點餐。系統支持多樣化的點餐表達，並能處理未知詞語，透過確認將其加入現有品項的同義詞庫，從而提升後續辨識準確率。

### 1.1 主要功能

- **即時語音辨識**：使用 Google Cloud Speech-to-Text 將客戶的語音輸入轉為文字。
- **點餐意圖識別**：使用 Rasa NLU 識別點餐語句，支持多種表達方式（例如「我要」、「給我」、「點」）。
- **未知詞語處理**：當客戶說出不在菜單中的詞語（例如「藍莓冰沙」），系統會猜測最相近的品項並詢問確認（例如「您說的是藍莓冰沙，是指草莓奶昔嗎？」）。
- **同義詞庫更新**：若客戶確認未知詞語是某現有品項的別名（例如「藍莓冰沙」對應「草莓奶昔」），系統將該詞語加入同義詞庫，後續直接映射到該品項。
- **限制範圍**：不支援新增全新菜單品項，僅更新現有品項的同義詞。

### 1.2 技術棧

- **語音辨識**：Google Cloud Speech-to-Text（串流模式）
- **NLP**：Rasa（開源 NLP 框架）
- **資料庫**：MongoDB（儲存菜單和同義詞）
- **後端**：Flask（整合語音和 Rasa）
- **其他**：PyAudio（錄音）、Levenshtein（詞語相似度計算）

---

## 2. 系統要求

### 2.1 硬體要求

- 作業系統：Windows、 macOS 或 Linux
- 記憶體：至少 4GB（建議 8GB）
- 儲存空間：至少 2GB
- 麥克風：用於語音輸入

### 2.2 軟體要求

- Python 3.8 或更高版本
- MongoDB 5.0 或更高版本
- Google Cloud Speech-to-Text API 憑證
- 依賴套件（詳見 `requirements.txt`）

### 2.3 環境配置

- **Google Cloud 設置**：

  1. 在 Google Cloud Console 創建專案並啟用 Speech-to-Text API。

  2. 建立服務帳戶，生成 JSON 憑證檔案。

  3. 設置環境變數：

     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
     ```

- **MongoDB 設置**：

  - 在本地或雲端運行 MongoDB 伺服器（預設 `mongodb://localhost:27017`）。
  - 確保伺服器可連線。

---

## 3. 安裝步驟

### 3.1 克隆項目

```bash
git clone <repository-url>
cd voice-ordering-system
```

### 3.2 安裝依賴

創建並啟動虛擬環境（可選）：

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

安裝依賴：

```bash
pip install -r requirements.txt
```

### 3.3 初始化菜單資料庫

運行 `init_db.py` 初始化 MongoDB 菜單：

```bash
python init_db.py
```

這將創建以下初始菜單：

- 大麥克（同義詞：麥克漢堡、大漢堡）
- 雞塊（無同義詞）
- 芒果冰沙（同義詞：芒果冰）
- 草莓奶昔（同義詞：草莓飲料）

### 3.4 訓練 Rasa 模型

運行以下命令訓練 Rasa NLU 和對話模型：

```bash
rasa train
```

訓練後的模型將儲存於 `models/` 資料夾。

---

## 4. 啟動系統

### 4.1 啟動 Rasa 伺服器

啟動 Rasa 的 REST API：

```bash
rasa run --enable-api
```

### 4.2 啟動自定義動作伺服器

在另一個終端機運行：

```bash
rasa run actions
```

### 4.3 啟動 Flask API

運行 Flask 應用程式，處理語音輸入：

```bash
python app.py
```

Flask 將在 `http://localhost:5000` 運行，接受 POST 請求到 `/order` 端點。

---

## 5. 使用方法

### 5.1 點餐流程

1. **語音輸入**：
   - 客戶透過麥克風說出點餐需求（例如「我要一個大麥克」或「給我一個藍莓冰沙」）。
   - 系統使用 Google Cloud Speech-to-Text 即時轉為文字。
2. **意圖識別**：
   - Rasa NLU 解析文字，識別意圖（`order`、`unknown_item` 等）和實體（`item`、`quantity`、`customization`）。
3. **未知詞語處理**：
   - 若輸入包含未知詞語（例如「藍莓冰沙」），系統猜測最相近的品項（例如「草莓奶昔」）並詢問確認。
   - 客戶回應「對，就是草莓奶昔」或「不是」。
4. **同義詞更新**：
   - 若確認，系統將未知詞語加入該品項的同義詞庫（例如「藍莓冰沙」→「草莓奶昔」）。
   - 後續輸入「藍莓冰沙」將直接映射到「草莓奶昔」。
5. **訂單確認**：
   - 系統回應訂單詳情（例如「您點了一份草莓奶昔，對嗎？」）。

### 5.2 API 使用

- **端點**：`POST /order`

- **請求範例**（模擬語音輸入）：

  ```bash
  curl -X POST http://localhost:5000/order
  ```

- **回應範例**（已知品項）：

  ```json
  {
    "text": "我要一個大麥克",
    "intent": "order",
    "entities": [{"entity": "item", "value": "大麥克"}],
    "response": "您點了一份大麥克，對嗎？"
  }
  ```

- **回應範例**（未知詞語）：

  ```json
  {
    "text": "我要一個藍莓冰沙",
    "intent": "unknown_item",
    "entities": [{"entity": "unknown_term", "value": "藍莓冰沙"}],
    "response": "您說的是藍莓冰沙，是指草莓奶昔嗎？"
  }
  ```

---

## 6. 測試用例

### 6.1 已知品項

- **輸入**：「我要一個大麥克」

- **預期輸出**：

  ```json
  {
    "text": "我要一個大麥克",
    "intent": "order",
    "entities": [{"entity": "item", "value": "大麥克"}],
    "response": "您點了一份大麥克，對嗎？"
  }
  ```

### 6.2 未知詞語（確認）

- **輸入 1**：「我要一個藍莓冰沙」

- **預期輸出 1**：

  ```json
  {
    "text": "我要一個藍莓冰沙",
    "intent": "unknown_item",
    "entities": [{"entity": "unknown_term", "value": "藍莓冰沙"}],
    "response": "您說的是藍莓冰沙，是指草莓奶昔嗎？"
  }
  ```

- **輸入 2**：「對，就是草莓奶昔」

- **預期輸出 2**：

  ```json
  {
    "text": "對，就是草莓奶昔",
    "intent": "confirm_item",
    "entities": [],
    "response": "好的，已將藍莓冰沙記為草莓奶昔的別名。您點了一份草莓奶昔，對嗎？"
  }
  ```

- **輸入 3**：「我要一個藍莓冰沙」

- **預期輸出 3**：

  ```json
  {
    "text": "我要一個藍莓冰沙",
    "intent": "order",
    "entities": [{"entity": "item", "value": "草莓奶昔"}],
    "response": "您點了一份草莓奶昔，對嗎？"
  }
  ```

### 6.3 未知詞語（否認）

- **輸入 1**：「我要一個藍莓冰沙」

- **預期輸出 1**：

  ```json
  {
    "text": "我要一個藍莓冰沙",
    "intent": "unknown_item",
    "entities": [{"entity": "unknown_term", "value": "藍莓冰沙"}],
    "response": "您說的是藍莓冰沙，是指草莓奶昔嗎？"
  }
  ```

- **輸入 2**：「不是」

- **預期輸出 2**：

  ```json
  {
    "text": "不是",
    "intent": "deny_item",
    "entities": [],
    "response": "抱歉，藍莓冰沙不在菜單中，請確認品項名稱或選擇其他餐點。"
  }
  ```

### 6.4 語音辨識失敗

- **輸入**：無效或無聲音輸入

- **預期輸出**：

  ```json
  {
    "error": "無法辨識語音"
  }
  ```

---

## 7. 維護與故障排除

### 7.1 常見問題

- **問題**：語音辨識失敗或準確率低
  - **解決**：
    - 檢查麥克風是否正常工作。
    - 確保環境噪音低，或加入 WebRTC 降噪。
    - 確認 Google Cloud 憑證有效。
- **問題**：Rasa 無法識別未知詞語
  - **解決**：
    - 檢查 `nlu.yml` 中的 `unknown_item` 意圖是否包含足夠的範例。
    - 調整 `actions.py` 中 Levenshtein 距離的閾值（預設 5）。
- **問題**：同義詞未正確更新
  - **解決**：
    - 檢查 MongoDB 連線（`mongodb://localhost:27017`）。
    - 確認 Rasa REST API 正在運行（`rasa run --enable-api`）。
    - 查看 `actions.py` 中的錯誤日誌。
- **問題**：系統延遲高
  - **解決**：
    - 快取 MongoDB 菜單資料，減少查詢次數。
    - 使用更高性能的伺服器或優化 Rasa 模型（減少 `config.yml` 中的訓練參數）。

### 7.2 日誌與監控

- **Rasa 日誌**：檢查 `rasa run` 和 `rasa run actions` 的終端輸出。
- **Flask 日誌**：檢查 `app.py` 的 `debug=True` 輸出。
- **MongoDB 日誌**：監控資料庫更新操作（例如同義詞新增）。
- 建議記錄所有未知詞語和確認結果，供後續分析。

### 7.3 備份

- 定期備份 MongoDB 資料庫（`menu_db.items` 集合）。
- 備份 `data/nlu.yml` 和 `models/` 資料夾，避免訓練數據或模型遺失。

---

## 8. 進階功能建議

- **多輪對話優化**：支援多次猜測品項（例如提供前兩個猜測選項）。
- **語音增強**：加入 WebRTC 降噪，適應高噪音環境（如餐廳現場）。
- **同義詞審核**：開發後台介面，讓店員審核新加入的同義詞。
- **多語言支援**：在 `nlu.yml` 中新增英文或其他語言的點餐語句。
- **日誌分析**：記錄常見未知詞語，優化 `unknown_item` 意圖的訓練數據。

---

## 9. 聯繫與支持

如需技術支援或客製化需求，請聯繫開發團隊：

- **電子郵件**：support@restaurant-tech.com
- **GitHub**：提交問題至項目倉庫（）

本說明書最後更新於 **2025年4月26日**。