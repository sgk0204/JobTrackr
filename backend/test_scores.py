import asyncio, httpx

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email':'test@example.com','password':'password123'})
        t = r.json()['access_token']
        r2 = await client.get('http://127.0.0.1:8000/api/v1/jobs/search?role=React&experience=2', headers={'Authorization':f"Bearer {t}"})
        data = r2.json()
        print("Length:", len(data.get("jobs", [])))
        for job in data.get("jobs", [])[:5]:
            print(f"Score: {job.get('ai_score')} - {job.get('title')} - {job.get('ai_reason')}")

asyncio.run(main())
