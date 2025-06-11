from fastapi import APIRouter, Depends, HTTPException, Cookie
from fastapi.responses import JSONResponse
from setup import redis_client
from blueprint.token import decrypt_token, verify_token
import json


payment = APIRouter(
    tags=["payment"],
)


@payment.get('/see_order')
async def see_order(ordering_token: str = Cookie(None)):
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
        order_state = json.loads(redis_client.get(f'{token_id}_order_state'))
        if not order_state:
            return JSONResponse(
                content={"error": "Order state not found"},
                status_code=404
            )

        return JSONResponse(
            content={"order_state": order_state},
            status_code=200
        )
    except Exception as e:
        print(f"Error retrieving order state: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve order state"},
            status_code=500
        )

@payment.post('/submit_payment')
async def submit_payment(ordering_token: str = Cookie(None)):
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
        order_state = json.loads(redis_client.get(f'{token_id}_order_state'))
        if not order_state:
            return JSONResponse(
                content={"error": "Order state not found"},
                status_code=404
            )

        # 假設支付邏輯在這裡
        order_state['payment']['status'] = 'paid'
        
        # 更新 Redis 中的訂單狀態
        redis_client.set(f'{token_id}_order_state', json.dumps(order_state))
        redis_client.delete(f'{token_id}_order_state', f'{token_id}_conversation')  # 清除之前的訂單狀態

        return JSONResponse(
            content={"msg": "Payment submitted successfully", "order_state": order_state},
            status_code=200
        )
    except Exception as e:
        print(f"Error submitting payment: {e}")
        return JSONResponse(
            content={"error": "Failed to submit payment"},
            status_code=500
        )

@payment.post('/clean_cookie')
async def clean_cookie(ordering_token: str = Cookie(None)):
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
        # 清除 Redis 中的訂單狀態和對話歷史
        redis_client.delete(f'{token_id}_order_state', f'{token_id}_conversation')
        response = JSONResponse(
            content={"msg": "Cookies cleaned successfully"},
            status_code=200
        )
        response.delete_cookie("ordering_token")  # 清除 cookie

        return response
    except Exception as e:
        print(f"Error cleaning cookies: {e}")
        return JSONResponse(
            content={"error": "Failed to clean cookies"},
            status_code=500
        )