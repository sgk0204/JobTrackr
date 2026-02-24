import os
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(user_id: str, email: str) -> str:
    utc_now = datetime.utcnow()
    expire = utc_now + timedelta(hours=JWT_EXPIRY_HOURS)
    
    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire,
        "iat": utc_now
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    
    # We will fetch full user details from DB in the route or just return the payload here.
    # The prompt says "returns user dict", so we'll return the payload containing user_id and email.
    # To be fully secure and up-to-date, one could fetch the user from the DB here,
    # but the prompt requirement: "Token payload must include: user_id, email, exp, iat"
    # "returns decoded payload or raises 401" for verify_token,
    # and "returns user dict" for get_current_user. 
    # Let's import get_db and fetch the user.
    from backend.database import db
    
    try:
        async with db.pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT id, email, name, avatar_url FROM users WHERE id = $1",
                payload.get("user_id")
            )
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return dict(user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        # Fallback to payload if db issues
        return {"id": payload.get("user_id"), "email": payload.get("email")}
