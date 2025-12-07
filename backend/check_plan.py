import asyncio
from app.database import AsyncSessionLocal, MasterPlan
from sqlalchemy import select

async def check_master_plan():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MasterPlan).where(MasterPlan.codebase_id == 'rocksdb'))
        plan = result.scalar_one_or_none()
        
        if plan:
            print(f"Master Plan Found: {plan.id}")
            print(f"Overview: {plan.plan_overview[:100]}...")
            if plan.weeks_data:
                print(f"Weeks: {len(plan.weeks_data)}")
                for w in plan.weeks_data:
                    print(f"Week {w.get('week_number')}: {w.get('title')}")
                    print(f"  Reading: {bool(w.get('reading_material'))}")
            else:
                print("Weeks Data is EMPTY or None")
        else:
            print("Master Plan NOT FOUND for 'rocksdb'")

if __name__ == "__main__":
    asyncio.run(check_master_plan())
