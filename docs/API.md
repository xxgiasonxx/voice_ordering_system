# API 文件

本系統 API 基於 FastAPI 建構，提供完整的 RESTful 介面。

## Base URL

```
http://localhost:8000
```

## 認證

所有需要認證的端點都需要攜帶 `ordering_token` Cookie。系統自動處理 Cookie，無需手動管理。

---

## 端點詳情

### GET /get-token

取得或刷新 session token。

**請求**
```
GET /get-token
```

**回應 (200)**
```json
{
  "msg": "set token successfully",
  "encrypted_token": "gAAAAABq..."
}
```

**說明**
- 首次呼叫時建立新 session
- 後續呼叫若 token 有效則返回 `"msg": "Token already set"`
- Token 有效期由 `TOKEN_EXPIRE_MINUTES` 設定

---

### GET /me

驗證當前 token 是否有效。

**請求**
```
GET /me
Cookie: ordering_token=<encrypted_token>
```

**回應 (200)**
```json
{
  "msg": "Token is valid"
}
```

---

### GET /menu

取得完整菜單。

**請求**
```
GET /menu
```

**回應 (200)**
```json
{
  "main": [
    {
      "id": 1,
      "class": "台式蛋餅",
      "name": "原味",
      "price": 30,
      "add_egg": true,
      "cheese": true,
      "kimchi": false,
      "roast": false,
      "cheese_milk": false,
      "danish": false,
      "combo": false,
      "vegetarian": false,
      "recommended": false
    }
  ],
  "combos": [
    {
      "id": 1,
      "name": "A套餐",
      "price": 100,
      "description": "蛋餅+飲料"
    }
  ],
  "drinks": [
    {
      "id": "1001",
      "class": "特調飲品",
      "name": "古早紅茶",
      "M": 20,
      "L": 30
    }
  ]
}
```

---

### POST /order/add-item

新增商品至購物車。

**請求**
```http
POST /order/add-item
Cookie: ordering_token=<encrypted_token>
Content-Type: application/json

{
  "item_id": 1,
  "quantity": 2,
  "customization_note": "加蛋、起司",
  "customization_price": 20
}
```

| 欄位 | 類型 | 必要 | 說明 |
|------|------|------|------|
| item_id | integer | 是 | 商品 ID (主餐 < 1000, 飲料 > 1000) |
| quantity | integer | 否 | 數量，預設 1 |
| customization_note | string | 否 | 客製化備註，預設 "無" |
| customization_price | integer | 否 | 客製化加價，預設 0 |

**回應 (200)**
```json
{
  "msg": "Item added to cart",
  "item": {
    "id": "11015",
    "item_id": 1,
    "class": "台式蛋餅",
    "name": "原味",
    "unitPrice": 30.0,
    "subtotal": 50.0,
    "quantity": 2,
    "customization": {
      "cus_price": 20,
      "note": "加蛋、起司"
    }
  },
  "order_state": { ... }
}
```

---

### POST /order/update-item

更新購物車商品數量。

**請求**
```http
POST /order/update-item
Cookie: ordering_token=<encrypted_token>
Content-Type: application/json

{
  "cart_item_id": "11015",
  "quantity": 3
}
```

| 欄位 | 類型 | 必要 | 說明 |
|------|------|------|------|
| cart_item_id | string | 是 | 購物車項目 ID |
| quantity | integer | 是 | 新數量 (設為 0 可刪除) |

**回應 (200)**
```json
{
  "msg": "Item updated",
  "order_state": { ... }
}
```

---

### POST /order/remove-item

移除購物車商品。

**請求**
```http
POST /order/remove-item
Cookie: ordering_token=<encrypted_token>
Content-Type: application/json

{
  "cart_item_id": "11015"
}
```

**回應 (200)**
```json
{
  "msg": "Item removed",
  "order_state": { ... }
}
```

---

### POST /order/clear-cart

清空購物車。

**請求**
```http
POST /order/clear-cart
Cookie: ordering_token=<encrypted_token>
```

**回應 (200)**
```json
{
  "msg": "Cart cleared",
  "order_state": {
    "order_id": "ORD202506151234",
    "order_time": "...",
    "items": [],
    "total_price": 0,
    ...
  }
}
```

---

### POST /order/ordering

語音點餐 (AI 處理)。

**請求**
```http
POST /order/ordering
Cookie: ordering_token=<encrypted_token>
Content-Type: application/json

{
  "text": "我要一份蛋餅加蛋和一杯大杯紅茶"
}
```

**回應 (200)**
```json
{
  "status_code": 200,
  "msg": "Order processed successfully",
  "response": "好的，已為您加入：1. 原味蛋餅(加蛋) 2. 古早紅茶(大杯)"
}
```

---

### GET /see_order

取得當前訂單狀態。

**請求**
```http
GET /see_order
Cookie: ordering_token=<encrypted_token>
```

**回應 (200)**
```json
{
  "order_state": {
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
        "customization": {
          "cus_price": 20,
          "note": "加蛋、起司"
        }
      }
    ],
    "total_price": 100.0,
    "payment": {"method": "現金", "status": "unpaid"},
    "order_type": "",
    "status": "start"
  }
}
```

---

### POST /submit_payment

提交付款。

**請求**
```http
POST /submit_payment
Cookie: ordering_token=<encrypted_token>
```

**回應 (200)**
```json
{
  "msg": "Payment submitted successfully",
  "order_state": {
    ...
    "payment": {"method": "現金", "status": "paid"}
  }
}
```

---

### POST /clean_cookie

清除 session。

**請求**
```http
POST /clean_cookie
Cookie: ordering_token=<encrypted_token>
```

**回應 (200)**
```json
{
  "msg": "Cookies cleaned successfully"
}
```

---

## 錯誤回應

| 狀態碼 | 說明 |
|--------|------|
| 400 | 請求格式錯誤 |
| 401 | 無效或過期的 token |
| 404 | 資源不存在 |
| 422 | 請求資料驗證失敗 |
| 500 | 伺服器內部錯誤 |

**錯誤格式**
```json
{
  "error": "Error message here"
}
```

---

## 測試範例

### Python 測試腳本

```python
#!/usr/bin/env python3
import urllib.request
import json

base = "http://localhost:8000"

# 1. 取得 token
req = urllib.request.Request(f"{base}/get-token")
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
resp = opener.open(req)
data = json.loads(resp.read())
token = data.get("encrypted_token", "")

# 2. 取得菜單
req = urllib.request.Request(f"{base}/menu")
resp = opener.open(req)
menu = json.loads(resp.read())
print(f"主餐數量: {len(menu['main'])}")

# 3. 加入購物車
add_data = json.dumps({
    "item_id": 1,
    "quantity": 2,
    "customization_note": "加蛋",
    "customization_price": 10
}).encode("utf-8")

req = urllib.request.Request(
    f"{base}/order/add-item",
    data=add_data,
    headers={"Content-Type": "application/json", "Cookie": f"ordering_token={token}"}
)
resp = opener.open(req)
result = json.loads(resp.read())
print(f"新增結果: {result['msg']}")

# 4. 查看訂單
req = urllib.request.Request(
    f"{base}/see_order",
    headers={"Cookie": f"ordering_token={token}"}
)
resp = opener.open(req)
order = json.loads(resp.read())
print(f"總金額: ${order['order_state']['total_price']}")
```