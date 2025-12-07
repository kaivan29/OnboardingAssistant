from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.config import get_settings

settings = get_settings()

Base = declarative_base()


# Database Models
class Candidate(Base):
    """Candidate/New Hire model"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    resume_text = Column(Text)
    resume_analysis = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodebaseConfig(Base):
    """Pre-configured codebase (e.g., RocksDB)"""
    __tablename__ = "codebase_configs"
    
    id = Column(String, primary_key=True)  # e.g., "rocksdb"
    name = Column(String, nullable=False)
    repository_url = Column(String, nullable=False)
    github_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodebaseAnalysis(Base):
    """Stored codebase analysis results (from daily job)"""
    __tablename__ = "codebase_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(String, index=True)
    analysis_data = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class LearningPlan(Base):
    """4-week personalized learning plan"""
    __tablename__ = "learning_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    codebase_id = Column(String)
    plan_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyContent(Base):
    """Weekly learning content"""
    __tablename__ = "weekly_content"
    
    id = Column(Integer, primary_key=True, index=True)
    learning_plan_id = Column(Integer, index=True)
    week_number = Column(Integer)
    reading_material = Column(JSON)
    coding_tasks = Column(JSON)
    quiz = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class MasterPlan(Base):
    """Pre-generated comprehensive master plan for a codebase"""
    __tablename__ = "master_plans"
    
    id = Column(String, primary_key=True)  # e.g., "rocksdb_v1"
    codebase_id = Column(String, index=True)
    version = Column(Integer, default=1)
    plan_overview = Column(Text)
    # Full 4-week plan with all reading, tasks, and quizzes
    weeks_data = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)



class Progress(Base):
    """Track candidate progress"""
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    week_number = Column(Integer)
    reading_completed = Column(JSON, default=[])  # Array of completed chapter numbers
    tasks_completed = Column(JSON, default=[])
    quiz_score = Column(Integer, nullable=True)
    quiz_answers = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
