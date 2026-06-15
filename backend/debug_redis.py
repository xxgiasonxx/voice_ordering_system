#!/usr/bin/env python3
import redis
import sys
sys.path.insert(0, '/app')
from setup import redis_client

print('Testing Redis connection from backend')
print(f'redis_client type: {type(redis_client)}')

# Try to get all keys
try:
    keys = redis_client.keys('*')
    print(f'All keys: {keys[:10]}')  # First 10 keys
except Exception as e:
    print(f'Error getting keys: {e}')

# Try to get a specific key pattern
try:
    order_keys = redis_client.keys('*order*')
    print(f'Order keys: {order_keys[:10]}')
except Exception as e:
    print(f'Error getting order keys: {e}')

# Try to get a token key
try:
    token_keys = redis_client.keys('*token*')
    print(f'Token keys: {token_keys[:10]}')
except Exception as e:
    print(f'Error getting token keys: {e}')