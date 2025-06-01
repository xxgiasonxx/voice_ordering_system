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

