import os
import logging
import httpx
import asyncio
from typing import List
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)
logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def parse_posted_time(time_text: str) -> datetime:
    """Converts strings like '2 days ago', '3 hours ago' to datetime."""
    now = datetime.now(timezone.utc)
    if not time_text:
        return now
        
    time_text = time_text.lower()
    try:
        val = int(''.join(filter(str.isdigit, time_text)) or 0)
        
        if 'hour' in time_text:
            return now - timedelta(hours=val)
        elif 'day' in time_text:
            return now - timedelta(days=val)
        elif 'week' in time_text:
            return now - timedelta(weeks=val)
        elif 'minute' in time_text:
            return now - timedelta(minutes=val)
    except Exception as e:
        logger.warning(f"Failed to parse time text '{time_text}': {e}")
        
    return now

def filter_recent_jobs(jobs: List[dict]) -> List[dict]:
    """Filters out jobs older than 24 hours."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    recent = []
    
    for job in jobs:
        posted_at = job.get('posted_at')
        if posted_at and posted_at >= cutoff:
            recent.append(job)
            
    return recent

async def _fetch_serpapi_jobs(client: httpx.AsyncClient, query: str) -> List[dict]:
    """Internal function to call SerpAPI with retries."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": "India",
        "chips": "date_posted:today",
        "hl": "en",
        "gl": "in",
        "api_key": SERPAPI_KEY
    }
    
    parsed_jobs = []
    for attempt in range(2):
        try:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            jobs = data.get("jobs_results", [])
            for job in jobs:
                source = "Unknown"
                if "via" in job and job["via"]:
                    source = job["via"].replace("via ", "").strip()
                    
                posted_time = parse_posted_time(job.get("detected_extensions", {}).get("posted_at", ""))
                
                ext_id = job.get("job_id")
                if not ext_id:
                    ext_id = f"fallback_{hash(job.get('title', ''))}_{hash(job.get('company_name', ''))}"
                
                parsed_jobs.append({
                    "external_id": ext_id,
                    "title": job.get("title"),
                    "company": job.get("company_name"),
                    "location": job.get("location"),
                    "description": job.get("description", ""),
                    "source": source,
                    "apply_url": job.get("apply_options", [{}])[0].get("link", "") if job.get("apply_options") else job.get("share_link", ""), 
                    "salary_range": job.get("detected_extensions", {}).get("salary", ""),
                    "posted_at": posted_time
                })
            break # Success, exit retry loop
            
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI HTTP Error (attempt {attempt+1}): {str(e)}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"SerpAPI Error (attempt {attempt+1}): {str(e)}")
            await asyncio.sleep(1)
            
    return parsed_jobs

async def fetch_jobs(role: str, experience: int, queries: List[str] = None) -> List[dict]:
    """
    Fetch jobs from SerpAPI. Support for fallback queries or parallel queries.
    """
    if not SERPAPI_KEY:
        logger.error("SERPAPI_KEY is not set")
        return []
        
    async with httpx.AsyncClient() as client:
        # If external optimized queries are provided (from Gemini Phase 4.2), run them in parallel
        if queries and len(queries) > 0:
            logger.info(f"Running parallel searches for optimized queries: {queries}")
            tasks = [_fetch_serpapi_jobs(client, q) for q in queries]
            results: List[List[dict]] = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_jobs = []
            seen_ids = set()
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"Parallel fetch error for '{queries[i]}': {res}")
                    continue
                for job in res:
                    if job["external_id"] not in seen_ids:
                        seen_ids.add(job["external_id"])
                        all_jobs.append(job)
            
            recent_jobs = filter_recent_jobs(all_jobs)
            logger.info(f"Parallel fetch returned {len(recent_jobs)} unique recent jobs")
            return recent_jobs

        # Otherwise, use Phase 8.2 sequential fallback logic
        base_queries = [
            f"{role} {experience} years experience jobs India",
            f"{role} jobs India",
            f"{role} hiring India 2024",
            f"{role} job opening Bangalore Mumbai Delhi"
        ]
        
        all_jobs = []
        for q in base_queries:
            logger.info(f"Trying SerpAPI query: {q}")
            all_jobs = await _fetch_serpapi_jobs(client, q)
            recent_jobs = filter_recent_jobs(all_jobs)
            if len(recent_jobs) > 0:
                logger.info(f"Query succeeded with {len(recent_jobs)} jobs.")
                return recent_jobs
                
        # If all fail, try without experience
        logger.info("All fallback queries failed, trying general query.")
        all_jobs = await _fetch_serpapi_jobs(client, f"{role} jobs India")
        recent_jobs = filter_recent_jobs(all_jobs)
        return recent_jobs
