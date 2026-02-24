import os
import logging
import asyncpg
from typing import AsyncGenerator
from fastapi import HTTPException
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool: asyncpg.Pool = None

    async def connect(self):
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable is not set")
            raise ValueError("DATABASE_URL environment variable is not set")
        
        try:
            logger.info("Connecting to database...")
            self.pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
                statement_cache_size=0
            )
            logger.info("Successfully connected to database pool.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise e

    async def disconnect(self):
        if self.pool:
            logger.info("Closing database pool...")
            await self.pool.close()
            logger.info("Database pool closed.")

db = Database()

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency to get a database connection from the pool"""
    if not db.pool:
        raise HTTPException(status_code=500, detail="Database pool is not initialized")
    
    async with db.pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database error during request processing: {str(e)}")
            raise

async def test_connection() -> bool:
    """Health check function for the database"""
    if not db.pool:
        return False
    try:
        async with db.pool.acquire() as connection:
            await connection.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
