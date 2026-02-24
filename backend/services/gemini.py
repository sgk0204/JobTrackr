import os
import json
import re
import asyncio
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# We use a global model instance or create it locally
# Using gemini-1.5-flash as specified

def safe_parse_json(text: str) -> Any:
    """Safely extracts and parses JSON from Gemini's response, handling markdown fences."""
    try:
        # Direct parsing
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    try:
        # Strip markdown code blocks
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
            
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text.strip())
    except json.JSONDecodeError:
        pass
        
    try:
        # Regex extraction
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            # Clean up trailing content after closing brace/bracket
            extracted = match.group(1)
            # Find the last closing bracket or brace
            last_bracket = extracted.rfind(']')
            last_brace = extracted.rfind('}')
            last_idx = max(last_bracket, last_brace)
            if last_idx != -1:
                extracted = extracted[:last_idx+1]
            return json.loads(extracted)
    except (json.JSONDecodeError, AttributeError):
        pass
        
    logger.error(f"Failed to parse JSON from Gemini response: {text[:100]}...")
    return None

async def rank_jobs(jobs: List[dict], role: str, experience: int, resume_text: str = None) -> List[dict]:
    """Score each job from 0-100 and add ai_score, ai_reason."""
    if not jobs:
        return []
    if not GEMINI_API_KEY:
        for j in jobs:
            j["ai_score"] = 50
            j["ai_reason"] = "AI ranking disabled (No API Key)"
        return jobs
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-8b') # using 8b if possible or just flash
        # We'll use the standard 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Limit to 30 jobs to save tokens
        slim_jobs = []
        for j in jobs[:30]:
            slim = {
                "id": str(j.get("external_id") or j.get("id")),
                "title": j.get("title"),
                "company": j.get("company"),
                "desc": j.get("description", "")[:200]
            }
            slim_jobs.append(slim)
            
        resume_context = ""
        if resume_text:
            resume_context = f"Also consider this candidate's resume summary:\n{resume_text[:1000]}\n"
            
        prompt = f"""
        Rank the following job listings for a '{role}' with {experience} years of experience in India.
        {resume_context}
        For each job, provide a relevance score (0-100) and a short 1-sentence reason.
        Respond ONLY with a JSON array of objects, containing 'id', 'score' (number), and 'reason' (string).
        Jobs:
        {json.dumps(slim_jobs)}
        """
        
        await asyncio.sleep(2) # rate limit prevention
        
        # We need an async wrapper or thread executor for Gemini since google.generativeai isn't fully async
        # But `generate_content_async` exists in modern SDK:
        response = await model.generate_content_async(prompt)
        
        parsed = safe_parse_json(response.text)
        if not parsed or not isinstance(parsed, list):
            raise Exception("Invalid JSON returned")
            
        logger.error(f"DEBUG - Parsed JSON: {parsed}")
        score_map = {str(item.get("id")): {"score": item.get("score", 50), "reason": item.get("reason", "Good match")} for item in parsed if isinstance(item, dict)}
        logger.error(f"DEBUG - Score Map: {score_map}")
        
        for j in jobs:
            # We must check against BOTH id and external_id string representations because Gemini could have returned either depending on the schema!
            ext_id = str(j.get("external_id", ""))
            db_id = str(j.get("id", ""))
            
            logger.error(f"DEBUG Loop - ext_id: {ext_id}, db_id: {db_id}, in map? {ext_id in score_map or db_id in score_map}")
            
            if ext_id and ext_id in score_map:
                j["ai_score"] = int(score_map[ext_id]["score"])
                j["ai_reason"] = score_map[ext_id]["reason"]
            elif db_id and db_id in score_map:
                j["ai_score"] = int(score_map[db_id]["score"])
                j["ai_reason"] = score_map[db_id]["reason"]
            else:
                j["ai_score"] = 50
                j["ai_reason"] = "Standard match"
                
        # Sort by ai_score descending
        jobs.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
        return jobs
        
    except Exception as e:
        import traceback
        logger.error(f"Gemini rank_jobs error: {str(e)}")
        logger.error(traceback.format_exc())
        for j in jobs:
            j["ai_score"] = 50
            j["ai_reason"] = "Ranking failed"
        return jobs

async def get_search_tips(role: str, experience: int) -> List[dict]:
    if not GEMINI_API_KEY:
        return [{"tip": "Tailor your resume.", "icon": "📝"}, {"tip": "Network on LinkedIn.", "icon": "🤝"}, {"tip": "Prepare for interviews.", "icon": "🎯"}]
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Provide exactly 3 concise job search tips for a {role} with {experience} years experience in India. Output strictly as JSON array with objects containing 'tip' (string) and 'icon' (emoji)."
        
        await asyncio.sleep(2)
        response = await model.generate_content_async(prompt)
        parsed = safe_parse_json(response.text)
        
        if parsed and isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except Exception as e:
        logger.error(f"Gemini get_search_tips error: {str(e)}")
        
    return [{"tip": "Tailor your resume.", "icon": "📝"}, {"tip": "Network on LinkedIn.", "icon": "🤝"}, {"tip": "Prepare for interviews.", "icon": "🎯"}]

async def generate_cover_letter(job: dict, user_name: str) -> str:
    if not GEMINI_API_KEY:
        return "Cover letter generation requires AI API key."
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Write a 3-paragraph personalized cover letter for {user_name} applying for the following job at {job.get('company')}.
        Job Title: {job.get('title')}
        Job Description snippet: {job.get('description', '')[:500]}
        Make it professional and concise.
        """
        
        await asyncio.sleep(2)
        response = await model.generate_content_async(prompt)
        if response.text:
            return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini generate_cover_letter error: {str(e)}")
        
    return "Error generating cover letter. Please try again."

async def optimize_search_queries(role: str, experience: int) -> List[str]:
    fallback = [f"{role} jobs India", f"{role} hiring India"]
    if not GEMINI_API_KEY:
        return fallback
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Generate exactly 5 optimized job search query variations for SerpAPI (Google Jobs) for a '{role}' with {experience} years experience in India.
        Consider synonyms, related titles, and seniority based on experience.
        Return ONLY a JSON array of strings. Do not include 'jobs' or 'India' in every single one if redundant, but keep intent clear.
        Example format: ["Query 1", "Query 2", ...]
        """
        
        await asyncio.sleep(2)
        response = await model.generate_content_async(prompt)
        parsed = safe_parse_json(response.text)
        
        if parsed and isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except Exception as e:
        logger.error(f"Gemini optimize_search_queries error: {str(e)}")
        
    return fallback
