import asyncio, json, os
from dotenv import load_dotenv
import google.generativeai as genai
from services.gemini import rank_jobs

load_dotenv(".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def main():
    jobs = [{'external_id': 'serp-id-5678', 'id': 'db-uuid-1234', 'title': 'DE_Application Engineer - I_VG_W5_PI Tech0268-Future Additional', 'company': 'Test Co', 'description': 'Need react devs.'}]
    ranked = await rank_jobs(jobs, 'React Developer', 2)
    print(f"Final AI Score assigned: {ranked[0].get('ai_score')}")
    print(f"Final AI Reason assigned: {ranked[0].get('ai_reason')}")
    print(f"Final Job Map: {ranked}")

if __name__ == "__main__":
    asyncio.run(main())
