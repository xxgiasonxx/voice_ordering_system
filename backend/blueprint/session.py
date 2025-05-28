from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from setup import init_order_state



auth = APIRouter()

async def set_order_state(request: Request):
    if "cus_id" not in request.session:
        import uuid
        request.session["cus_id"] = str(uuid.uuid4())
    if 'order_state' not in request.session:
        request.session['order_state'] = init_order_state()

