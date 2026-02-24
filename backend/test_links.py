import asyncio, httpx
async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email':'test@example.com','password':'password123'})
        t = r.json()['access_token']
        r2 = await client.get('http://127.0.0.1:8000/api/v1/jobs/search?role=Python&experience=3', headers={'Authorization': f'Bearer {t}'})
        data = r2.json()
        jobs = data.get('jobs', [])
        print(f"Total jobs: {len(jobs)}")
        for j in jobs[:3]:
            print(f"Title: {j['title']} | Apply URL: {j.get('apply_url')}")
if __name__ == '__main__':
    asyncio.run(main())
