#!/usr/bin/env python3
import urllib.request
import json

base = "http://localhost:8000"

# Step 1: Get token
req = urllib.request.Request(f"{base}/get-token")
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
resp = opener.open(req)
data = json.loads(resp.read())
token = data.get("encrypted_token", "")
print(f"Token: {token[:50]}...")

# Step 2: Add item to cart
add_data = json.dumps({
    "item_id": 1,
    "quantity": 2,
    "customization_note": "加蛋、起司",
    "customization_price": 20
}).encode("utf-8")

req = urllib.request.Request(
    f"{base}/order/add-item",
    data=add_data,
    headers={"Content-Type": "application/json", "Cookie": f"ordering_token={token}"}
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read())
    print(f"Add item result: {json.dumps(result, indent=2, ensure_ascii=False)}")
except urllib.error.HTTPError as e:
    print(f"Add item error: {e.code} - {e.read()}")

# Step 3: See order
req = urllib.request.Request(
    f"{base}/see_order",
    headers={"Cookie": f"ordering_token={token}"}
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read())
    print(f"\nSee order: {json.dumps(result, indent=2, ensure_ascii=False)}")
except urllib.error.HTTPError as e:
    print(f"See order error: {e.code} - {e.read()}")

# Step 4: Add a drink
add_data = json.dumps({
    "item_id": 1001,
    "quantity": 1,
    "customization_note": "無",
    "customization_price": 0
}).encode("utf-8")

req = urllib.request.Request(
    f"{base}/order/add-item",
    data=add_data,
    headers={"Content-Type": "application/json", "Cookie": f"ordering_token={token}"}
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read())
    print(f"\nAdd drink result: {json.dumps(result, indent=2, ensure_ascii=False)}")
except urllib.error.HTTPError as e:
    print(f"Add drink error: {e.code} - {e.read()}")

# Step 5: Final see order
req = urllib.request.Request(
    f"{base}/see_order",
    headers={"Cookie": f"ordering_token={token}"}
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read())
    print(f"\nFinal order: {json.dumps(result, indent=2, ensure_ascii=False)}")
except urllib.error.HTTPError as e:
    print(f"Final see order error: {e.code} - {e.read()}")