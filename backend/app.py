import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.sessions import SessionMiddleware
from blueprint.order import order
from blueprint.orderSocket import audioWS
from blueprint.token import token
from blueprint.payment import payment
import os

# 初始化 FastAPI 應用
app = FastAPI()

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # 添加 Session 中間件
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=os.getenv('SECRET_KEY', "your_secret_key_here"),
#     max_age=int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600)),
#     session_cookie=os.getenv('SESSION_COOKIE_NAME', 'order_session'),
#     https_only=os.getenv("HTTPS_ONLY", "false").lower() == "true",
#     same_site="lax"
# )


# 包含路由
app.include_router(order, prefix="/order")
app.include_router(token)
app.include_router(audioWS)
app.include_router(payment)

if __name__ == '__main__':
    uvicorn.run(app, host='loaclhost', port=8000)
