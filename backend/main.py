import os
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.database import db, test_connection
from backend.services.cache import cache_service
from backend.auth.router import router as auth_router
from backend.routes.jobs import router as jobs_router
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = FastAPI(
    title="JobTrackr API",
    description="Backend API for JobTrackr AI-Powered Job Search Portal",
    version="1.0.0",
    docs_url="/docs"
)

# CORS config
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Simple console logger
    status_code = response.status_code
    print(f"[{request.method}] {request.url.path} - {status_code} - {duration:.3f}s")
    
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    print(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

@app.on_event("startup")
async def startup_event():
    print("Initializing Database Pool...")
    await db.connect()
    
    print("Testing Redis Connection...")
    redis_ok = await cache_service.is_healthy()
    print(f"Redis Status: {'Connected' if redis_ok else 'Failed'}")

@app.on_event("shutdown")
async def shutdown_event():
    print("Closing Database Pool...")
    await db.disconnect()

@app.get("/health")
async def health_check():
    db_ok = await test_connection()
    redis_ok = await cache_service.is_healthy()
    
    return {
        "status": "up" if db_ok else "downgraded",
        "db": "connected" if db_ok else "error",
        "redis": "connected" if redis_ok else "error",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ping")
async def ping():
    """Keep-alive strategy for Render.com free tier"""
    return {"pong": True}

app.include_router(auth_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
