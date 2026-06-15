#!/usr/bin/env python3
import redis
import json

r = redis.Redis(host='redis', port=6379)
key = b'056d6ea4-2d31-465e-8c05-f46913067976_order_state'
print('Key exists:', r.exists(key))
val = r.get(key)
print('Value type:', type(val))
print('Value:', val)
if val:
    parsed = json.loads(val)
    print('Parsed:', json.dumps(parsed, indent=2, ensure_ascii=False)[:500])