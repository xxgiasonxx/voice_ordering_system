from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from rag.rag_morning_eat import order_real_time
from setup import cus_choice, vectorstore, conn

# Create APIRouter instead of Blueprint
order = APIRouter(prefix="/order", tags=["ordering"])

# Pydantic model for request body
class OrderRequest(BaseModel):
    text: str

# Simple in-memory session storage (replace with proper session management)
session_store = {}

def get_session():
    return session_store

@order.post('/')
async def ordering(request: OrderRequest, session: dict = Depends(get_session)):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail='No text provided')
        
        order_state = session.get('order_state', None)
        response, order_state = order_real_time(
            request.text, 
            vectorstore=vectorstore, 
            cus_choice=cus_choice, 
            order_state=order_state, 
            conn=conn
        )
        session['order_state'] = order_state
        
        return {'response': response, 'order_state': order_state}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail='Invalid request format')