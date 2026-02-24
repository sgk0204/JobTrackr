import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from backend.database import get_db
from backend.auth.jwt_handler import create_access_token, get_current_user
import asyncpg

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    google_token: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: SignupRequest, db: asyncpg.Connection = Depends(get_db)):
    # Check if email exists
    existing_user = await db.fetchval("SELECT id FROM users WHERE email = $1", user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pwd = get_password_hash(user_data.password)
    
    # Insert new user
    row = await db.fetchrow(
        """
        INSERT INTO users (email, name, password_hash)
        VALUES ($1, $2, $3)
        RETURNING id, email, name, avatar_url
        """,
        user_data.email, user_data.name, hashed_pwd
    )
    
    access_token = create_access_token(row['id'], row['email'])
    
    return {
        "access_token": access_token,
        "user": dict(row)
    }

@router.post("/login")
async def login(credentials: LoginRequest, db: asyncpg.Connection = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT id, email, name, avatar_url, password_hash FROM users WHERE email = $1",
        credentials.email
    )
    
    if not user or not user['password_hash']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    access_token = create_access_token(user['id'], user['email'])
    
    return {
        "access_token": access_token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "avatar_url": user['avatar_url']
        }
    }

@router.post("/google")
async def google_auth(request: GoogleLoginRequest, db: asyncpg.Connection = Depends(get_db)):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            request.google_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get("email")
        name = idinfo.get("name")
        google_id = idinfo.get("sub")
        picture = idinfo.get("picture")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # 1. Check if user exists by google_id
        user = await db.fetchrow(
            "SELECT id, email, name, avatar_url FROM users WHERE google_id = $1",
            google_id
        )
        
        if user:
            access_token = create_access_token(user['id'], user['email'])
            return {"access_token": access_token, "user": dict(user)}
            
        # 2. Check if user exists by email (link accounts)
        user_by_email = await db.fetchrow(
            "SELECT id, email, name, avatar_url FROM users WHERE email = $1",
            email
        )
        
        if user_by_email:
            # Link Google ID
            updated_user = await db.fetchrow(
                """
                UPDATE users SET google_id = $1, avatar_url = COALESCE(avatar_url, $2)
                WHERE id = $3
                RETURNING id, email, name, avatar_url
                """,
                google_id, picture, user_by_email['id']
            )
            access_token = create_access_token(updated_user['id'], updated_user['email'])
            return {"access_token": access_token, "user": dict(updated_user)}
            
        # 3. Neither -> create new user
        new_user = await db.fetchrow(
            """
            INSERT INTO users (email, name, google_id, avatar_url)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, name, avatar_url
            """,
            email, name, google_id, picture
        )
        
        access_token = create_access_token(new_user['id'], new_user['email'])
        return {"access_token": access_token, "user": dict(new_user)}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
