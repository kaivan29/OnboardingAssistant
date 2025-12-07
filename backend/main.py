from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.database import init_db, AsyncSessionLocal, CodebaseConfig
from app.routes import router

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered onboarding platform using Grok - Pre-configured for RocksDB",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Initialize SQLite database
    await init_db()
    print("✓ Database initialized")
    
    # Initialize RocksDB as pre-configured codebase
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CodebaseConfig).where(CodebaseConfig.id == 'rocksdb'))
        rocksdb_config = result.scalar_one_or_none()
        
        if not rocksdb_config:
            rocksdb_config = CodebaseConfig(
                id='rocksdb',
                name='RocksDB',
                repository_url='https://github.com/facebook/rocksdb',
                github_token=None
            )
            db.add(rocksdb_config)
            await db.commit()
            print("✓ RocksDB codebase configuration initialized")
    
    # Start master plan scheduler (runs every hour)
    from app.scheduler import master_plan_scheduler
    master_plan_scheduler.start()
    print("✓ Master plan scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from app.scheduler import master_plan_scheduler
    master_plan_scheduler.shutdown()
    print("✓ Master plan scheduler stopped")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],  # Allow all origins for Cloud Run
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Grok Onboarding Platform API",
        "status": "running",
        "version": "1.0.0",
        "pre_configured_codebase": "RocksDB (https://github.com/facebook/rocksdb)",
        "note": "New hires will learn the RocksDB codebase through personalized AI-generated curriculum"
    }


@app.get("/health")
async def health():
    """Health check for Cloud Run"""
    return {"status": "healthy"}
