#!/usr/bin/env python3
import urllib.request
import json

base = 'http://localhost:8000'

# Get token
req = urllib.request.Request(f'{base}/get-token')
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor)
resp = opener.open(req)
data = json.loads(resp.read())
token = data.get('encrypted_token', '')
print(f'Token: {token[:50]}...')

# Add item
add_data = json.dumps({
    'item_id': 1,
    'quantity': 1,
    'customization_note': '無',
    'customization_price': 0
}).encode('utf-8')

req = urllib.request.Request(
    f'{base}/order/add-item',
    data=add_data,
    headers={'Content-Type': 'application/json', 'Cookie': f'ordering_token={token}'}
)
resp = opener.open(req)
result = json.loads(resp.read())
order_state = result.get('order_state', {})
print(f'Order ID: {order_state.get("order_id", "NO_ORDER_ID")}')
print(f'Items in order: {len(order_state.get("items", []))}')
print(f'Total price: {order_state.get("total_price", 0)}')

# Now let's directly check Redis by calling see_order with the same token
req = urllib.request.Request(
    f'{base}/payment/see_order',
    headers={'Cookie': f'ordering_token={token}'}
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read())
    print(f'See order success!')
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
except urllib.error.HTTPError as e:
    body = e.read()
    print(f'See order error: {e.code} - {body}')