import asyncio
import httpx

async def test_search():
    async with httpx.AsyncClient() as client:
        # Create user / login
        print("Logging in...")
        res = await client.post("http://127.0.0.1:8000/api/v1/auth/signup", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        })
        if res.status_code == 400 and "already registered" in res.text:
            res = await client.post("http://127.0.0.1:8000/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
        
        token = res.json().get("access_token")
        print(f"Token acquired. Testing search...")
        
        # Test search
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get(
            "http://127.0.0.1:8000/api/v1/jobs/search?role=Full+Stack+Developer&experience=2",
            headers=headers,
            timeout=60.0
        )
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:1000]}")

if __name__ == "__main__":
    asyncio.run(test_search())
