import asyncio
from app.database import AsyncSessionLocal, CodebaseConfig, CodebaseAnalysis
from app.services.plan_template_service import plan_template_service
from app.services.codebase_analyzer import codebase_analyzer
from sqlalchemy import select

async def setup_rocksdb():
    print("Checking RocksDB configuration...")
    codebase_url = "https://github.com/facebook/rocksdb"
    codebase_id = codebase_url # ID is same as URL in some places, or just "rocksdb"
    # Actually schema says ID is String. Routes use codebase_url as ID.
    
    async with AsyncSessionLocal() as db:
        # 1. Check Config
        result = await db.execute(select(CodebaseConfig).where(CodebaseConfig.repository_url == codebase_url))
        config = result.scalar_one_or_none()
        
        if not config:
            print("Creating CodebaseConfig...")
            # Use URL as ID to match frontend
            config = CodebaseConfig(
                id=codebase_url,
                name="RocksDB",
                repository_url=codebase_url
            )
            db.add(config)
            await db.commit()
            codebase_id = codebase_url
        else:
            print(f"CodebaseConfig exists with ID: {config.id}")
            codebase_id = config.id


        # 2. Check Analysis
        result = await db.execute(select(CodebaseAnalysis).where(CodebaseAnalysis.codebase_id == codebase_url))
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            print(f"Triggering Codebase Analysis for {codebase_id} (this might take a while)...")
            # We will use the service directly
            await codebase_analyzer.analyze_configured_codebase(codebase_id)
            print("Analysis complete.")
        else:
            print("CodebaseAnalysis exists.")
            
        # 3. Generate Master Plan
        print(f"Generating Master Plan for {codebase_id}...")
        await plan_template_service.generate_master_plan(codebase_id, db)
        print("Master Plan generated successfully!")

if __name__ == "__main__":
    asyncio.run(setup_rocksdb())
