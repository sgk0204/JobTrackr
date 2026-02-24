import asyncio
import os
import asyncpg
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")

async def alter_db():
    print(f"Connecting to database to alter schema...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("Executing ALTER queries...")
        await conn.execute("""
            ALTER TABLE jobs ALTER COLUMN external_id TYPE TEXT;
            ALTER TABLE jobs ALTER COLUMN title TYPE TEXT;
            ALTER TABLE jobs ALTER COLUMN company TYPE TEXT;
            ALTER TABLE jobs ALTER COLUMN location TYPE TEXT;
            ALTER TABLE jobs ALTER COLUMN salary_range TYPE TEXT;
        """)
        print("Schema execution complete.")
        await conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    asyncio.run(alter_db())
