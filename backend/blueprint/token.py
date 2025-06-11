from fastapi import APIRouter, WebSocket, HTTPException, Response, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from typing import Optional
import uvicorn
import uuid
from dotenv import load_dotenv
import os
import json
import logging
from setup import redis_client ,init_order_state
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

token = APIRouter()

# JWT 設定
SECRET_KEY = os.getenv('SECRET_KEY', "your_secret_key_here")
ALGORITHM = os.getenv('ALGORITHM', "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv('TOKEN_EXPIRE_MINUTES', 30))

# Fernet 加密設定
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())  # 實際應用中應儲存在環境變數
cipher = Fernet(FERNET_KEY)

@token.get("/me")
async def test_me(request: Request):
    try:
        token_id = request.cookies.get("ordering_token")
        token = decrypt_token(token_id)
        t = await verify_token(token)
        logger.info(f"Token verified successfully: {t}")
        return JSONResponse(
            content={"msg": "Token is valid"},
            status_code=200
        )
    except HTTPException as e:
        logger.error(f"Token verification failed: {e.detail}")
        return JSONResponse(
            content={"msg": "Token verification failed"},
            status_code=e.status_code
        )


# 生成 JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 加密 token
def encrypt_token(token: str) -> str:
    return cipher.encrypt(token.encode()).decode()

# 解密 token
def decrypt_token(encrypted_token: str) -> str:
    try:
        return cipher.decrypt(encrypted_token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid encrypted token")

# 驗證 JWT token
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id: str = payload.get("sub")
        # 檢查 Redis 中是否存在該 token
        if not redis_client.exists(token_id):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return token_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@token.get("/get-token")
async def get_token(request: Request):
    if "ordering_token" in request.cookies:
        logger.info("Access token already exists in cookies.")
        encrypted_token = request.cookies.get("ordering_token")
        decrypted_token = decrypt_token(encrypted_token)
        token_id = await verify_token(decrypted_token)
        if not redis_client.exists(f"{token_id}_order_state"):
            logger.info("Initializing order state for existing token.")
            redis_client.setex(f"{token_id}_order_state", TOKEN_EXPIRE_MINUTES * 60, json.dumps(init_order_state()))

        if not redis_client.exists(f"{token_id}_conversation"):
            logger.info("Initializing conversation for existing token.")
            redis_client.setex(f"{token_id}_conversation", TOKEN_EXPIRE_MINUTES * 60, json.dumps([
            {
                "type": "llm",
                "response": "您好！歡迎使用語音點餐系統，請參考上方菜單並告訴我您想要什麼餐點？",
                "time": datetime.now().isoformat()
            }
        ]))
        return JSONResponse(
            content={"msg": "Token already set"},
            status_code=200
        )
    try:
        token_id = str(uuid.uuid4())
        access_token_expires = timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": token_id}, expires_delta=access_token_expires
        )
        redis_client.setex(token_id, TOKEN_EXPIRE_MINUTES * 60, "valid")
        redis_client.setex(f"{token_id}_order_state", TOKEN_EXPIRE_MINUTES * 60, json.dumps(init_order_state()))
        redis_client.setex(f"{token_id}_conversation", TOKEN_EXPIRE_MINUTES * 60, json.dumps([
            {
                "type": "llm",
                "response": "您好！歡迎使用語音點餐系統，請參考上方菜單並告訴我您想要什麼餐點？",
                "time": datetime.now().isoformat()
            }
        ]))

        encrypted_token = encrypt_token(access_token)
        logger.info(f"Setting cookie with encrypted_token: {encrypted_token}")
        response = JSONResponse(
            content={"msg": "set token successfully", "encrypted_token": encrypted_token},
            status_code=200
        )
        response.set_cookie(
            key="ordering_token",
            value=encrypted_token,
            httponly=True,
            secure=False,  # 本地開發設為 False，生產環境設為 True
            samesite="strict",  # 可根據需要調整
            expires=TOKEN_EXPIRE_MINUTES * 60,
        )
        return response
    except Exception as e:
        logger.error(f"Error in get_token: {e}")
        raise HTTPException(status_code=500, detail=str(e))
