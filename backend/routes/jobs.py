from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncpg
from typing import List, Optional
from backend.database import get_db
from backend.auth.jwt_handler import get_current_user
from backend.services.scraper import fetch_jobs
from backend.services.cache import cache_service
from backend.services.gemini import rank_jobs, get_search_tips, optimize_search_queries
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class StatusUpdate(BaseModel):
    status: str

@router.get("/search")
async def search_jobs(
    role: str,
    experience: int,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Check Cache
    cached_jobs = await cache_service.get_cached_jobs(role, experience)
    cached_tips = await cache_service.get_cached_tips(role, experience)
    
    if cached_jobs is not None:
        if cached_tips is None:
            cached_tips = await get_search_tips(role, experience)
        return {
            "jobs": cached_jobs,
            "ai_tips": cached_tips,
            "from_cache": True,
            "total": len(cached_jobs)
        }
        
    # 2. Optimize Queries
    queries = await optimize_search_queries(role, experience)
    
    # 3. Fetch from SerpAPI
    new_jobs = await fetch_jobs(role, experience, queries=queries)
    if not new_jobs:
        return {"jobs": [], "ai_tips": [], "from_cache": False, "total": 0}
        
    # 4. Save to DB (Upsert)
    # Build batch upsert data
    db_jobs = []
    for job in new_jobs:
        # Avoid duplicate external_ids in the same batch
        row = await db.fetchrow(
            """
            INSERT INTO jobs (external_id, title, company, location, description, source, apply_url, salary_range, posted_at, experience_min)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (external_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                apply_url = EXCLUDED.apply_url,
                source = EXCLUDED.source,
                fetched_at = now()
            RETURNING id, external_id, title, company, location, description, source, apply_url, salary_range, posted_at
            """,
            job["external_id"], job["title"], job["company"], job.get("location"), job.get("description"),
            job.get("source"), job.get("apply_url"), job.get("salary_range"), job.get("posted_at"), experience
        )
        if row:
            job_dict = dict(row)
            job_dict["id"] = str(job_dict["id"])
            db_jobs.append(job_dict)

    print(f"DEBUG API jobs passed to rank_jobs: {db_jobs}")

    # 5. AI Rank Results
    ranked_jobs = await rank_jobs(db_jobs, role, experience)
    ai_tips = await get_search_tips(role, experience)
    
    # Format dates to string for caching compatibility
    for j in ranked_jobs:
        if j.get("posted_at"):
            j["posted_at"] = j["posted_at"].isoformat()
            
    # 6. Cache Results
    await cache_service.cache_jobs(role, experience, ranked_jobs)
    await cache_service.cache_tips(role, experience, ai_tips)
    
    return {
        "jobs": ranked_jobs,
        "ai_tips": ai_tips,
        "from_cache": False,
        "total": len(ranked_jobs)
    }

@router.post("/apply/{job_id}", status_code=status.HTTP_201_CREATED)
async def apply_job(
    job_id: str,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        await db.execute(
            """
            INSERT INTO applied_jobs (user_id, job_id, status)
            VALUES ($1, $2, 'applied')
            """,
            current_user["id"], job_id
        )
        return {"message": "Successfully applied to job"}
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Already applied to this job")

@router.patch("/apply/{job_id}/status")
async def update_application_status(
    job_id: str,
    update: StatusUpdate,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if update.status not in ['applied', 'inprocess', 'rejected', 'hired']:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    res = await db.execute(
        """
        UPDATE applied_jobs SET status = $1, updated_at = now()
        WHERE user_id = $2 AND job_id = $3
        """,
        update.status, current_user["id"], job_id
    )
    if res == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Job application not found")
    return {"message": "Status updated"}

@router.delete("/apply/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_application(
    job_id: str,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await db.execute(
        "DELETE FROM applied_jobs WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )

@router.post("/save/{job_id}", status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: str,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        await db.execute(
            """
            INSERT INTO saved_jobs (user_id, job_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            current_user["id"], job_id
        )
        return {"message": "Job saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/save/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: str,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await db.execute(
        "DELETE FROM saved_jobs WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )

@router.get("/my-jobs")
async def my_jobs(
    filter: str = Query("all"),
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Base joins
    query = """
    SELECT 
        j.id, j.title, j.company, j.location, j.source, j.apply_url, j.salary_range,
        aj.status, aj.applied_at, aj.updated_at,
        sj.saved_at
    FROM jobs j
    LEFT JOIN applied_jobs aj ON j.id = aj.job_id AND aj.user_id = $1
    LEFT JOIN saved_jobs sj ON j.id = sj.job_id AND sj.user_id = $1
    WHERE (aj.id IS NOT NULL OR sj.id IS NOT NULL)
    """
    
    if filter == 'saved':
        query += " AND sj.id IS NOT NULL AND aj.id IS NULL"
    elif filter == 'applied':
        query += " AND aj.id IS NOT NULL"
    elif filter in ['inprocess', 'rejected', 'hired']:
        query += f" AND aj.status = '{filter}'"

    query += " ORDER BY COALESCE(aj.updated_at, sj.saved_at) DESC"
    
    rows = await db.fetch(query, current_user["id"])
    
    # Calculate summary counts
    summary = {"applied": 0, "inprocess": 0, "rejected": 0, "hired": 0, "saved": 0}
    all_jobs_user = await db.fetch("""
        SELECT status, COUNT(*) as c FROM applied_jobs WHERE user_id = $1 GROUP BY status
    """, current_user["id"])
    for r in all_jobs_user:
        if r['status'] in summary:
            summary[r['status']] = r['c']
            
    saved_count = await db.fetchval("SELECT COUNT(*) FROM saved_jobs WHERE user_id = $1 AND job_id NOT IN (SELECT job_id FROM applied_jobs WHERE user_id = $1)", current_user["id"])
    summary["saved"] = saved_count or 0
    
    return {
        "jobs": [dict(r) for r in rows],
        "summary": summary
    }

@router.get("/{job_id}")
async def get_job_details(
    job_id: str,
    db: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    job = await db.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    applied = await db.fetchrow("SELECT status, applied_at FROM applied_jobs WHERE user_id = $1 AND job_id = $2", current_user["id"], job_id)
    saved = await db.fetchrow("SELECT saved_at FROM saved_jobs WHERE user_id = $1 AND job_id = $2", current_user["id"], job_id)
    
    res = dict(job)
    res["user_data"] = {
        "applied": bool(applied),
        "status": applied["status"] if applied else None,
        "applied_at": applied["applied_at"] if applied else None,
        "saved": bool(saved),
        "saved_at": saved["saved_at"] if saved else None
    }
    
    return res
