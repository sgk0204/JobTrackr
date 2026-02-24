import asyncio, httpx, os
from dotenv import load_dotenv
from services.scraper import _fetch_serpapi_jobs

load_dotenv('.env')

async def main():
    async with httpx.AsyncClient() as client:
        jobs = await _fetch_serpapi_jobs(client, "React jobs India")
        for j in jobs[:3]:
            print(f"Title: {j['title']} | Orig Link: {j.get('apply_url')}")

if __name__ == '__main__':
    asyncio.run(main())
