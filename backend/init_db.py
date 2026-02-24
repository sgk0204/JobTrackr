import asyncio
import os
import asyncpg
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    print(f"Connecting to database to run schema...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql'), 'r') as f:
            schema = f.read()
            
        print("Executing schema.sql...")
        await conn.execute(schema)
        print("Schema execution complete.")
        await conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
