import asyncio
from app.database import engine, Base
from sqlalchemy import text

async def clear_candidate_data():
    print("Starting database cleanup...")
    async with engine.begin() as conn:
        # Disable foreign key checks to avoid deletion order issues (SQLite specific)
        await conn.execute(text("PRAGMA foreign_keys = OFF"))
        
        # Tables to clear
        tables_to_clear = [
            "progress",
            "weekly_content",
            "learning_plans",
            "candidates"
        ]
        
        for table in tables_to_clear:
            print(f"Clearing table: {table}")
            await conn.execute(text(f"DELETE FROM {table}"))
            
        # Re-enable foreign keys
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        
    print("Database cleanup complete. Master plans preserved.")

if __name__ == "__main__":
    asyncio.run(clear_candidate_data())
