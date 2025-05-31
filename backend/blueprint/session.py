from fastapi import APIRouter, HTTPException, UploadFile, File, Request
# from setup import init_order_state
# from setup import redis_client, init_order_state

auth = APIRouter()


# async def set_order_state(request: Request):
#     if "cus_id" not in request.session:
#         import uuid
#         request.session["cus_id"] = str(uuid.uuid4())
#         request.cookie.set('cus_id', request.session["cus_id"], httponly=True, samesite='lax')
#     if redis_client.get(f'{request.session.get('cus_id')}_order_state', None) is None:
#         redis_client.set(f'{request.session.get('cus_id')}_order_state', init_order_state())

