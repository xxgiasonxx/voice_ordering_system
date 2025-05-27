from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from setup import init_order_state

auth = APIRouter()

# Session management
def get_session(request: Request):
    if not hasattr(request.state, 'session'):
        request.session = {}
    return request.session

@auth.get('/setorder')
def set_order_state(request: Request):
    if 'order_state' not in request.session:
        request.session['order_state'] = jsonable_encoder(init_order_state())
    response = {
        "msg": "Order state initialized",
        "order_state": jsonable_encoder(request.session['order_state'])
    }
    return JSONResponse(content=jsonable_encoder(response), status_code=status.HTTP_200_OK)