import os
import json
import logging
from typing import List, Optional
import redis.asyncio as redis
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)
logger = logging.getLogger(__name__)

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")

class CacheService:
    def __init__(self):
        self.redis = None
        if UPSTASH_REDIS_URL:
            try:
                self.redis = redis.from_url(UPSTASH_REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")

    def _get_key(self, prefix: str, role: str, experience: int) -> str:
        role_fmt = role.lower().replace(" ", "_").strip()
        return f"{prefix}:{role_fmt}:{experience}"

    async def get_cached_jobs(self, role: str, experience: int) -> Optional[List[dict]]:
        return None

    async def cache_jobs(self, role: str, experience: int, jobs: List[dict]) -> None:
        if not self.redis: return
        try:
            key = self._get_key("jobs", role, experience)
            # 6 hours = 21600 seconds
            await self.redis.setex(key, 21600, json.dumps(jobs, default=str)) # default=str for datetime
        except Exception as e:
            logger.error(f"Redis cache jobs error: {str(e)}")

    async def get_cached_tips(self, role: str, experience: int) -> Optional[List[dict]]:
        if not self.redis: return None
        try:
            key = self._get_key("tips", role, experience)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get tips error: {str(e)}")
            return None

    async def cache_tips(self, role: str, experience: int, tips: List[dict]) -> None:
        if not self.redis: return
        try:
            key = self._get_key("tips", role, experience)
            await self.redis.setex(key, 21600, json.dumps(tips))
        except Exception as e:
            logger.error(f"Redis cache tips error: {str(e)}")

    async def clear_cache(self, role: str, experience: int) -> None:
        if not self.redis: return
        try:
            jobs_key = self._get_key("jobs", role, experience)
            tips_key = self._get_key("tips", role, experience)
            await self.redis.delete(jobs_key, tips_key)
        except Exception as e:
            logger.error(f"Redis clear cache error: {str(e)}")

    async def is_healthy(self) -> bool:
        if not self.redis: return False
        try:
            return await self.redis.ping()
        except Exception:
            return False

cache_service = CacheService()
