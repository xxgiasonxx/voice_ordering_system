from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn, redis_client
from blueprint.token import decrypt_token, verify_token
import json

# Create APIRouter instead of Blueprint
order = APIRouter(
    tags=["ordering"],
)

# Pydantic model for request body
class OrderRequest(BaseModel):
    text: str

# Pydantic models for cart operations
class CartItemRequest(BaseModel):
    item_id: int
    quantity: int = 1
    customization_note: str = "無"
    customization_price: int = 0

class CartItemUpdateRequest(BaseModel):
    cart_item_id: str
    quantity: int

class CartItemDeleteRequest(BaseModel):
    cart_item_id: str


def _get_item_from_db(item_id: int, conn):
    """Query item from PostgreSQL or SQLite."""
    from rag.CRUD_database import create_connection
    if conn is None:
        conn = create_connection()
    cur = conn.cursor()

    if item_id > 1000:
        cur.execute("SELECT id, class, name, M as price, M, L FROM drink_item WHERE id = %s::text", (str(item_id),))
    else:
        cur.execute("SELECT id, class, name, price FROM main_menu WHERE id = %s", (item_id,))

    row = cur.fetchone()
    if not row:
        return None

    if isinstance(row, dict):
        return row
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, row))


def _verify_token(token: str) -> str:
    """Verify token and return token_id."""
    import asyncio
    from jose import JWTError
    import concurrent.futures

    decrypted = None
    try:
        decrypted = decrypt_token(token)
    except JWTError as e:
        print(f"JWT decode error: {e}")
        raise ValueError(f"Invalid token format: {e}")
    except Exception as e:
        print(f"Unexpected error in decrypt_token: {e}")
        raise ValueError(f"Token decryption failed: {e}")

    print(f"[DEBUG] _verify_token: decrypted token, using ThreadPoolExecutor")
    with concurrent.futures.ThreadPoolExecutor() as pool:
        token_id = pool.submit(asyncio.run, verify_token(decrypted)).result()
    print(f"[DEBUG] _verify_token: token_id = {token_id}")
    return token_id


def _add_item_to_order_state(order_state: dict, item: dict, quantity: int, customizations: str, cus_price: int) -> dict:
    """Add or update item in order_state."""
    item_price = item.get('price', item.get('M', 0))
    item_id = item.get('id')

    for existing_item in order_state["items"]:
        if existing_item['item_id'] == item_id and existing_item['customization']['note'] == customizations:
            existing_item['quantity'] += quantity
            order_state['total_price'] += existing_item['subtotal'] * quantity
            return order_state

    import random
    order_state["items"].append({
        "id": str(item_id) + str(random.randint(1000, 9999)),
        "item_id": item_id,
        "class": item.get('class', '套餐'),
        "name": item.get('name', '未知'),
        "unitPrice": item_price,
        "subtotal": item_price + cus_price,
        "quantity": quantity,
        "customization": {
            "cus_price": cus_price,
            "note": customizations,
        }
    })
    order_state['total_price'] += (item_price + cus_price) * quantity
    return order_state


@order.post('/add-item')
async def add_cart_item(item: CartItemRequest, ordering_token: str = Cookie(None)):
    """Add item to cart via REST API."""
    try:
        token_id = _verify_token(ordering_token)
    except Exception as e:
        return JSONResponse(content={"error": "Invalid or expired token"}, status_code=401)

    try:
        item_data = _get_item_from_db(item.item_id, conn)
        if not item_data:
            return JSONResponse(content={"error": "Item not found"}, status_code=404)

        order_state = json.loads(redis_client.get(f'{token_id}_order_state') or '{"items":[],"total_price":0,"status":"ongoing"}')

        order_state = _add_item_to_order_state(
            order_state, item_data, item.quantity, item.customization_note, item.customization_price
        )

        redis_client.set(f'{token_id}_order_state', json.dumps(order_state))

        return JSONResponse(content={
            "msg": "Item added to cart",
            "item": order_state["items"][-1],
            "order_state": order_state
        }, status_code=200)
    except Exception as e:
        print(f"Error adding item: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@order.post('/update-item')
async def update_cart_item(item: CartItemUpdateRequest, ordering_token: str = Cookie(None)):
    """Update item quantity in cart."""
    try:
        token_id = _verify_token(ordering_token)
    except Exception as e:
        return JSONResponse(content={"error": "Invalid or expired token"}, status_code=401)

    try:
        order_state = json.loads(redis_client.get(f'{token_id}_order_state') or '{"items":[],"total_price":0,"status":"ongoing"}')

        for existing_item in order_state["items"]:
            if existing_item['id'] == item.cart_item_id:
                quantity_diff = item.quantity - existing_item['quantity']
                existing_item['quantity'] = item.quantity
                order_state['total_price'] += existing_item['subtotal'] * quantity_diff
                if existing_item['quantity'] <= 0:
                    order_state["items"].remove(existing_item)
                break

        redis_client.set(f'{token_id}_order_state', json.dumps(order_state))

        return JSONResponse(content={"msg": "Item updated", "order_state": order_state}, status_code=200)
    except Exception as e:
        print(f"Error updating item: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@order.post('/remove-item')
async def remove_cart_item(item: CartItemDeleteRequest, ordering_token: str = Cookie(None)):
    """Remove item from cart."""
    try:
        token_id = _verify_token(ordering_token)
    except Exception as e:
        return JSONResponse(content={"error": "Invalid or expired token"}, status_code=401)

    try:
        order_state = json.loads(redis_client.get(f'{token_id}_order_state') or '{"items":[],"total_price":0,"status":"ongoing"}')

        for existing_item in order_state["items"]:
            if existing_item['id'] == item.cart_item_id:
                order_state['total_price'] -= existing_item['subtotal'] * existing_item['quantity']
                order_state["items"].remove(existing_item)
                break

        redis_client.set(f'{token_id}_order_state', json.dumps(order_state))

        return JSONResponse(content={"msg": "Item removed", "order_state": order_state}, status_code=200)
    except Exception as e:
        print(f"Error removing item: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@order.post('/clear-cart')
async def clear_cart(ordering_token: str = Cookie(None)):
    """Clear all items from cart."""
    try:
        token_id = _verify_token(ordering_token)
    except Exception as e:
        return JSONResponse(content={"error": "Invalid or expired token"}, status_code=401)

    try:
        from rag.rag_morning_eat import init_order_state
        empty_state = init_order_state()
        redis_client.set(f'{token_id}_order_state', json.dumps(empty_state))
        return JSONResponse(content={"msg": "Cart cleared", "order_state": empty_state}, status_code=200)
    except Exception as e:
        print(f"Error clearing cart: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)



@order.post('/ordering')
async def ordering(OrderRequest: OrderRequest, ordering_token: str = Cookie(None)):
    try:
        # Decrypt and verify the token
        token = decrypt_token(ordering_token)
        token_id = await verify_token(token)
        if not token_id:
            raise HTTPException(status_code=401, detail='Invalid or expired token')
    except Exception as e:
        print(f"Token verification failed: {e}")
        return JSONResponse(
            content={"error": "Invalid or expired token"},
            status_code=401
        )

    try:
        if not OrderRequest.text:
            return JSONResponse(
                content={"error": "No text provided"},
                status_code=400
            )
        
        order_state = json.loads(redis_client.get(f'{token_id}_order_state'))

        response, order_state, order_diff = order_real_time(
            query=OrderRequest.text, 
            vectorstore=vectorstore, 
            cus_choice=cus_choice, 
            order_state=order_state, 
            conn=conn
        )
        result = {
            'status_code': 200,
            'msg': 'Order processed successfully',
            'response': response,
        }
        
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail='Invalid request format')

