"""
Periodic job scheduler for refreshing master plans.

Runs hourly to keep master plans up-to-date with latest codebase analysis.
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal, CodebaseConfig, Candidate
from app.services.plan_template_service import plan_template_service
from app.services.grok_service import grok_service

logger = logging.getLogger(__name__)


async def analyze_pending_resumes():
    """Background job to analyze resumes that are pending analysis"""
    async with AsyncSessionLocal() as db:
        # Find candidates without resume analysis
        result = await db.execute(
            select(Candidate).where(Candidate.resume_analysis == None).limit(5)  # Process 5 at a time
        )
        pending_candidates = result.scalars().all()
        
        if not pending_candidates:
            return  # Nothing to do
        
        logger.info(f"🔍 Found {len(pending_candidates)} candidates with pending resume analysis")
        
        for candidate in pending_candidates:
            try:
                logger.info(f"📋 Analyzing resume for candidate {candidate.id} ({candidate.name})...")
                analysis = await grok_service.analyze_resume(candidate.resume_text)
                
                # Update candidate with analysis
                candidate.resume_analysis = analysis
                await db.commit()
                
                logger.info(f"✅ Completed resume analysis for candidate {candidate.id}")
            except Exception as e:
                logger.error(f"❌ Failed to analyze resume for candidate {candidate.id}: {str(e)}")
                # Don't commit on failure, will retry next run
                await db.rollback()


def resume_analysis_job():
    """Sync wrapper for resume analysis job"""
    asyncio.run(analyze_pending_resumes())


def master_plan_job():
    """Generate/update master plans for all configured codebases"""
    async def run():
        async with AsyncSessionLocal() as db:
            try:
                # Get all configured code bases
                result = await db.execute(select(CodebaseConfig))
                codebases = result.scalars().all()
                
                logger.info(f"🔄 Starting master plan refresh for {len(codebases)} codebases")
                
                for codebase in codebases:
                    try:
                        logger.info(f"  📚 Refreshing master plan for {codebase.name} ({codebase.id})")
                        
                        master_plan = await plan_template_service.generate_master_plan(
                            codebase.id,
                            db
                        )
                        
                        logger.info(f"  ✅ Master plan updated: {master_plan['id']}")
                        
                    except Exception as e:
                        logger.error(f"  ❌ Failed to refresh master plan for {codebase.id}: {str(e)}")
                
                logger.info("✅ Master plan refresh completed")
                
            except Exception as e:
                logger.error(f"❌ Master plan refresh job failed: {str(e)}")
    
    asyncio.run(run())


class MasterPlanScheduler:
    """Manages periodic background jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        # Master plan refresh - runs hourly
        self.scheduler.add_job(
            master_plan_job,
            trigger=IntervalTrigger(hours=1),
            id='refresh_master_plans',
            name='Refresh Master Plans',
            replace_existing=True
        )
        
        # Resume analysis - runs every 30 seconds
        self.scheduler.add_job(
            resume_analysis_job,
            trigger=IntervalTrigger(seconds=30),
            id='analyze_resumes',
            name='Analyze Pending Resumes',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("🚀 Background scheduler started")
        logger.info("   - Master plan refresh: every hour")
        logger.info("   - Resume analysis: every 30 seconds")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("⏹️  Background scheduler stopped")


# Singleton instance
master_plan_scheduler = MasterPlanScheduler()
