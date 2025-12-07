import asyncio
import os
import tempfile
import shutil
from git import Repo
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy import select

from app.database import AsyncSessionLocal, CodebaseConfig, CodebaseAnalysis
from app.services.grok_service import grok_service


class CodebaseAnalyzer:
    """Service for analyzing pre-configured codebases (e.g., RocksDB GitHub repo)"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    async def clone_and_analyze(self, codebase_url: str, github_token: str = None) -> Dict[str, Any]:
        """Clone repository and perform analysis"""
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Clone repository
            print(f"Cloning {codebase_url}...")
            if github_token:
                url_parts = codebase_url.replace('https://', '').split('/')
                auth_url = f"https://{github_token}@{'/'.join(url_parts)}"
                repo = Repo.clone_from(auth_url, temp_dir, depth=1)
            else:
                repo = Repo.clone_from(codebase_url, temp_dir, depth=1)
            
            # Analyze codebase structure
            analysis = await self._analyze_local_codebase(temp_dir, codebase_url)
            
            return analysis
            
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    async def _analyze_local_codebase(self, repo_path: str, repo_url: str) -> Dict[str, Any]:
        """Analyze local codebase directory"""
        # Get basic repository statistics
        file_count = 0
        language_stats = {}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', 'dist', 'build']]
            
            for file in files:
                file_count += 1
                ext = os.path.splitext(file)[1]
                if ext:
                    language_stats[ext] = language_stats.get(ext, 0) + 1
        
        # Use Grok to analyze the codebase
        analysis = await grok_service.analyze_codebase(repo_url)
        
        # Enhance with local stats
        analysis['local_stats'] = {
            'file_count': file_count,
            'language_distribution': language_stats,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        return analysis
    
    async def analyze_configured_codebase(self, codebase_id: str):
        """Analyze a pre-configured codebase and save results to SQLite"""
        print(f"Starting analysis for codebase: {codebase_id}")
        
        async with AsyncSessionLocal() as db:
            # Get codebase configuration
            result = await db.execute(
                select(CodebaseConfig).where(CodebaseConfig.id == codebase_id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                print(f"Codebase {codebase_id} not found")
                return
            
            try:
                # Perform analysis
                analysis_data = await self.clone_and_analyze(
                    config.repository_url,
                    config.github_token
                )
                
                # Save analysis results
                analysis = CodebaseAnalysis(
                    codebase_id=codebase_id,
                    analysis_data=analysis_data,
                    analyzed_at=datetime.utcnow()
                )
                
                db.add(analysis)
                await db.commit()
                
                print(f"Successfully analyzed codebase: {codebase_id}")
                
            except Exception as e:
                print(f"Error analyzing codebase {codebase_id}: {str(e)}")
                await db.rollback()
    
    def analyze_all_codebases(self):
        """Analyze all pre-configured codebases (called by scheduler)"""
        print(f"[{datetime.utcnow()}] Running daily codebase analysis...")
        
        # Run analysis in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._analyze_all_async())
        loop.close()
    
    async def _analyze_all_async(self):
        """Async method to analyze all codebases"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(CodebaseConfig))
            codebases = result.scalars().all()
            
            for config in codebases:
                try:
                    await self.analyze_configured_codebase(config.id)
                except Exception as e:
                    print(f"Error analyzing {config.id}: {str(e)}")
    
    def start_scheduler(self):
        """Start the background scheduler for daily analysis"""
        # Run analysis daily at 2 AM
        self.scheduler.add_job(
            self.analyze_all_codebases,
            trigger='cron',
            hour=2,
            minute=0,
            id='daily_codebase_analysis'
        )
        
        self.scheduler.start()
        print("Codebase analysis scheduler started (runs daily at 2 AM)")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Codebase analysis scheduler stopped")


# Global instance
codebase_analyzer = CodebaseAnalyzer()
