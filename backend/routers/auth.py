from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
from database import get_bot_config

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    password: str

TOKEN_EXPIRATION_HOURS = 24

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def login(request: LoginRequest):
    # Получаем пароль из настроек бота
    config = get_bot_config()
    admin_password = os.getenv("ADMIN_PANEL_PASSWORD", config.get("admin_panel_password", "admin123"))

    if request.password != admin_password:
        raise HTTPException(status_code=401, detail="Wrong password")

    access_token = create_access_token(data={"sub": "admin"})
    return {"token": access_token, "token_type": "bearer"}

@router.get("/verify")
async def verify_token_endpoint(payload: dict = Depends(verify_token)):
    return {"valid": True, "user": payload["sub"]}