from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn

# Create APIRouter instead of Blueprint
order = APIRouter(
    tags=["ordering"],
)

# Pydantic model for request body
class OrderRequest(BaseModel):
    text: str

# Simple in-memory session storage (replace with proper session management)
session_store = {}

def get_session():
    return session_store

@order.post('/ordering')
async def ordering(request: Request, OrderRequest: OrderRequest):
    print("Received order request:", OrderRequest.text)
    try:
        print(OrderRequest)
        if not OrderRequest.text:
            raise HTTPException(status_code=400, detail='No text provided')
        
        order_state = request.session.get('order_state', None)
        if not order_state:
            raise HTTPException(status_code=400, detail='Order state not initialized. Please set order state first.')
        response, order_state = order_real_time(
            OrderRequest.text, 
            vectorstore=vectorstore, 
            cus_choice=cus_choice, 
            order_state=order_state, 
            conn=conn
        )
        request.session['order_state'] = order_state
        result = {
            'status_code': 200,
            'msg': 'Order processed successfully',
            'response': response,
        }
        
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail='Invalid request format')

