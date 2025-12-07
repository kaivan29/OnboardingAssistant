from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
import PyPDF2
import io
import asyncio
from pathlib import Path
import copy
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db, Candidate, CodebaseConfig, CodebaseAnalysis, LearningPlan, WeeklyContent, Progress, MasterPlan
from app.schema import (
    CandidateCreate, CandidateResponse, LearningPlanCreate, LearningPlanResponse,
    WeeklyContentResponse, ProgressUpdate
)
from app.services.grok_service import grok_service
from app.services.codebase_analyzer import codebase_analyzer

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/upload-resume", response_model=CandidateResponse)
async def upload_resume(
    file: UploadFile = File(...),
    name: str = None,
    email: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Upload resume - analysis happens in background"""
    import time
    start_time = time.time()
    
    # Extract name from filename if not provided (e.g., "elon_musk.pdf" -> "Elon Musk")
    if not name and file.filename:
        # Remove .pdf extension and replace underscores with spaces
        filename_without_ext = file.filename.replace('.pdf', '').replace('.PDF', '')
        # Replace underscores/hyphens with spaces and title case
        extracted_name = filename_without_ext.replace('_', ' ').replace('-', ' ').title()
        name = extracted_name
    
    # Extract text from PDF
    try:
        print(f"📄 Reading PDF file: {file.filename}")
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
        read_time = time.time() - start_time
        print(f"✓ PDF read successfully ({len(resume_text)} chars) in {read_time:.2f}s")
    except Exception as e:
        print(f"❌ Failed to read PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")
    
    # Check if we've already processed this exact resume (cache based on resume text)
    result = await db.execute(
        select(Candidate).where(Candidate.resume_text == resume_text).limit(1)
    )
    existing_candidate = result.scalar_one_or_none()
    
    if existing_candidate:
        # Return existing candidate (analysis may be pending or complete)
        print(f"✨ Found existing candidate with same resume (ID: {existing_candidate.id})")
        total_time = time.time() - start_time
        print(f"✅ Resume upload completed in {total_time:.2f}s (cached)")
        return existing_candidate
    
    # Create new candidate without analysis (analysis happens in background)
    candidate = Candidate(
        name=name or "Unknown",
        email=email or f"{name.lower().replace(' ', '.')}@example.com" if name else f"candidate_{hash(resume_text[:100])}@example.com",
        resume_text=resume_text,
        resume_analysis=None  # Will be filled by background job
    )
    
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    
    total_time = time.time() - start_time
    print(f"✅ Resume uploaded instantly in {total_time:.2f}s - analysis will happen in background")
    print(f"   Candidate: {candidate.name} (ID: {candidate.id})")
    
    return candidate


@router.get("/codebases")
async def list_codebases(db: AsyncSession = Depends(get_db)):
    """List all pre-configured codebases"""
    result = await db.execute(select(CodebaseConfig))
    codebases = result.scalars().all()
    return codebases


@router.post("/codebases")
async def add_codebase(
    codebase_id: str,
    name: str,
    repository_url: str,
    github_token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Add a new pre-configured codebase"""
    codebase = CodebaseConfig(
        id=codebase_id,
        name=name,
        repository_url=repository_url,
        github_token=github_token
    )
    
    db.add(codebase)
    await db.commit()
    
    # Trigger immediate analysis
    await codebase_analyzer.analyze_configured_codebase(codebase_id)
    
    return {'message': 'Codebase added and analysis started', 'codebase_id': codebase_id}


@router.post("/analyze-codebase/{codebase_id}")
async def trigger_analysis(codebase_id: str):
    """Manually trigger codebase analysis"""
    await codebase_analyzer.analyze_configured_codebase(codebase_id)
    return {'message': 'Analysis triggered', 'codebase_id': codebase_id}


@router.get("/codebase-analysis/{codebase_id}")
async def get_codebase_analysis(codebase_id: str, db: AsyncSession = Depends(get_db)):
    """Get latest codebase analysis"""
    result = await db.execute(
        select(CodebaseAnalysis)
        .where(CodebaseAnalysis.codebase_id == codebase_id)
        .order_by(desc(CodebaseAnalysis.analyzed_at))
        .limit(1)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis.analysis_data


@router.post("/generate-plan", response_model=LearningPlanResponse)
async def generate_learning_plan(request: LearningPlanCreate, db: AsyncSession = Depends(get_db)):
    """
    Generate personalized 4-week learning plan FAST using pre-generated templates.
    This is 10x faster than the old approach!
    """
    from app.services.plan_template_service import plan_template_service
    
    # Get candidate
    result = await db.execute(select(Candidate).where(Candidate.id == request.candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if not candidate.resume_analysis:
        raise HTTPException(status_code=400, detail="Resume must be analyzed first")
    
    # Check for existing learning plan (cache) unless force_regenerate is True
    if not request.force_regenerate:
        result = await db.execute(
            select(LearningPlan).where(
                LearningPlan.candidate_id == request.candidate_id,
                LearningPlan.codebase_id == request.codebase_url
            ).order_by(desc(LearningPlan.created_at)).limit(1)
        )
        existing_plan = result.scalar_one_or_none()
        
        # Return cached plan if it exists and is recent (within 7 days)
        if existing_plan:
            from datetime import timedelta
            age = datetime.utcnow() - existing_plan.created_at
            if age < timedelta(days=7):
                print(f"✨ Reusing existing learning plan (created {age.days} days ago)")
                
                response = LearningPlanResponse(
                    id=existing_plan.id,
                    candidate_id=existing_plan.candidate_id,
                    codebase_url=existing_plan.codebase_id,
                    weeks=[
                        {
                            "week_number": w["week_number"],
                            "title": w["title"],
                            "objectives": w.get("objectives", []),
                            "topics": w.get("topics", [])
                        }
                        for w in existing_plan.plan_data.get("weeks", [])
                    ],
                    created_at=existing_plan.created_at
                )
                return response
            else:
                print(f"⚠️  Existing plan is {age.days} days old, regenerating...")
    else:
        print(f"🔄 Force regenerate flag set, creating new plan...")
    
    try:
        # FAST PATH: Use pre-generated master plan
        master_plan = await plan_template_service.get_master_plan(request.codebase_url, db)
        
        if master_plan:
            print(f"✨ Using pre-generated master plan for {request.codebase_url}")
            
            # Quick personalization based on resume (1 API call, ~3-5 seconds)
            personalized = await plan_template_service.personalize_plan(
                master_plan,
                candidate.resume_analysis
            )
            
            # Create learning plan record
            learning_plan = LearningPlan(
                candidate_id=candidate.id,
                codebase_id=request.codebase_url,
                plan_data={
                    "overview": personalized["overview"],
                    "recommendations": personalized.get("recommendations", []),
                    "weeks": [
                        {
                            "week_number": w["week_number"],
                            "title": w["title"],
                            "objectives": w.get("objectives", []),
                            "topics": w.get("topics", []),
                            "focus_areas": w.get("focus_areas", [])
                        }
                        for w in personalized["weeks"]
                    ]
                }
            )
            
            db.add(learning_plan)
            await db.commit()
            await db.refresh(learning_plan)
            
            # Create weekly content from master plan
            for week_data in personalized["weeks"]:
                weekly_content = WeeklyContent(
                    learning_plan_id=learning_plan.id,
                    week_number=week_data["week_number"],
                    reading_material=week_data.get("reading_material", {}),
                    coding_tasks=week_data.get("coding_tasks", []),
                    quiz=week_data.get("quiz", [])
                )
                db.add(weekly_content)
            
            await db.commit()
            
            response = LearningPlanResponse(
                id=learning_plan.id,
                candidate_id=learning_plan.candidate_id,
                codebase_url=learning_plan.codebase_id,
                weeks=[
                    {
                        "week_number": w["week_number"],
                        "title": w["title"],
                        "objectives": w.get("objectives", []),
                        "topics": w.get("topics", [])
                    }
                    for w in learning_plan.plan_data.get("weeks", [])
                ],
                created_at=learning_plan.created_at
            )
            
            return response
        
        else:
            print(f"⚠️  No master plan found for {request.codebase_url}, falling back to slow generation")
            
            # SLOW FALLBACK: Generate from scratch (old approach)
            # Get codebase analysis
            result = await db.execute(
                select(CodebaseAnalysis)
                .where(CodebaseAnalysis.codebase_id == request.codebase_url)
                .order_by(desc(CodebaseAnalysis.analyzed_at))
                .limit(1)
            )
            analysis_record = result.scalar_one_or_none()
            
            if analysis_record:
                codebase_analysis = analysis_record.analysis_data
            else:
                codebase_analysis = await grok_service.analyze_codebase(
                    request.codebase_url,
                    request.github_token
                )
            
            # Generate plan from scratch
            plan_data = await grok_service.generate_learning_plan(
                candidate.resume_analysis,
                codebase_analysis
            )
            
            learning_plan = LearningPlan(
                candidate_id=candidate.id,
                codebase_id=request.codebase_url,
                plan_data=plan_data
            )
            
            db.add(learning_plan)
            await db.commit()
            await db.refresh(learning_plan)
            
            # Generate content for all 4 weeks
            for week in plan_data.get("weeks", []):
                week_number = week["week_number"]
                
                try:
                    reading = await grok_service.generate_weekly_reading(week, codebase_analysis)
                    tasks = await grok_service.generate_coding_tasks(week, codebase_analysis)
                    quiz = await grok_service.generate_quiz(week, reading.get("content", ""))
                    
                    weekly_content = WeeklyContent(
                        learning_plan_id=learning_plan.id,
                        week_number=week_number,
                        reading_material=reading,
                        coding_tasks=tasks,
                        quiz=quiz
                    )
                    
                    db.add(weekly_content)
                except Exception as e:
                    print(f"Warning: Failed to generate content for week {week_number}: {str(e)}")
            
            await db.commit()
            
            response = LearningPlanResponse(
                id=learning_plan.id,
                candidate_id=learning_plan.candidate_id,
                codebase_url=learning_plan.codebase_id,
                weeks=[
                    {
                        "week_number": w["week_number"],
                        "title": w["title"],
                        "objectives": w["objectives"],
                        "topics": w.get("topics", [])
                    }
                    for w in plan_data.get("weeks", [])
                ],
                created_at=learning_plan.created_at
            )
            
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")



@router.get("/plan/{candidate_id}", response_model=LearningPlanResponse)
async def get_learning_plan(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Get learning plan for a candidate"""
    result = await db.execute(
        select(LearningPlan)
        .where(LearningPlan.candidate_id == candidate_id)
        .order_by(desc(LearningPlan.created_at))
        .limit(1)
    )
    learning_plan = result.scalar_one_or_none()
    
    if not learning_plan:
        raise HTTPException(status_code=404, detail="Learning plan not found")
    
    plan_data = learning_plan.plan_data
    
    response = LearningPlanResponse(
        id=learning_plan.id,
        candidate_id=learning_plan.candidate_id,
        codebase_url=learning_plan.codebase_id,
        weeks=[
            {
                "week_number": w["week_number"],
                "title": w["title"],
                "objectives": w["objectives"],
                "topics": w.get("topics", [])
            }
            for w in plan_data.get("weeks", [])
        ],
        created_at=learning_plan.created_at
    )
    
    return response


@router.get("/study-plan/{candidate_id}")
async def get_study_plan(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Get complete study plan with all weekly content (similar to /api/master-plan/{codebase_id})"""
    # Get learning plan
    result = await db.execute(
        select(LearningPlan).where(LearningPlan.candidate_id == candidate_id).order_by(desc(LearningPlan.created_at)).limit(1)
    )
    learning_plan = result.scalar_one_or_none()
    
    if not learning_plan:
        raise HTTPException(status_code=404, detail="No study plan found for this candidate")
    
    # Get all weekly content
    result = await db.execute(
        select(WeeklyContent).where(WeeklyContent.learning_plan_id == learning_plan.id).order_by(WeeklyContent.week_number)
    )
    weekly_contents = result.scalars().all()
    
    # Combine plan with weekly content
    weeks_data = []
    for week in learning_plan.plan_data.get("weeks", []):
        week_number = week["week_number"]
        
        # Find corresponding weekly content
        weekly_content = next((wc for wc in weekly_contents if wc.week_number == week_number), None)
        
        week_data = {
            "week_number": week_number,
            "title": week["title"],
            "objectives": week.get("objectives", []),
            "topics": week.get("topics", []),
            "focus_areas": week.get("focus_areas", []),
        }
        
        if weekly_content:
            week_data.update({
                "reading_material": weekly_content.reading_material,
                "coding_tasks": weekly_content.coding_tasks,
                "quiz": weekly_content.quiz
            })
        
        weeks_data.append(week_data)
    
    return {
        "id": f"study_plan_{candidate_id}_{learning_plan.id}",
        "candidate_id": candidate_id,
        "codebase_id": learning_plan.codebase_id,
        "overview": learning_plan.plan_data.get("overview", ""),
        "recommendations": learning_plan.plan_data.get("recommendations", []),
        "weeks": weeks_data,
        "created_at": learning_plan.created_at.isoformat() if learning_plan.created_at else None
    }




@router.get("/week/{candidate_id}/{week_number}", response_model=WeeklyContentResponse)
async def get_weekly_content(
    candidate_id: int,
    week_number: int,
    db: AsyncSession = Depends(get_db)
):
    """Get weekly content (reading, tasks, quiz) - uses master plan or generates on-demand"""
    # Get learning plan
    result = await db.execute(
        select(LearningPlan)
        .where(LearningPlan.candidate_id == candidate_id)
        .order_by(desc(LearningPlan.created_at))
        .limit(1)
    )
    learning_plan = result.scalar_one_or_none()
    
    if not learning_plan:
        raise HTTPException(status_code=404, detail="Learning plan not found")
    
    # Get weekly content
    result = await db.execute(
        select(WeeklyContent).where(
            WeeklyContent.learning_plan_id == learning_plan.id,
            WeeklyContent.week_number == week_number
        )
    )
    weekly_content = result.scalar_one_or_none()
    
    # Get candidate to determine expectations
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    expectation_context = None
    if candidate and candidate.resume_analysis:
        try:
            level = candidate.resume_analysis.get("experience_level", "junior").lower()
            if "senior" in level or "staff" in level or "lead" in level:
                prompt_file = "senior_engineer_prompt.md"
            else:
                prompt_file = "junior_engineer_prompt.md"
                
            base_path = Path(__file__).parent.parent / "expectation_prompts"
            prompt_path = base_path / prompt_file
            
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    expectation_context = f.read()
        except Exception as e:
            print(f"Error loading expectation: {e}")

    # If weekly content doesn't exist or is empty, try to get from master plan first
    if not weekly_content or not weekly_content.reading_material or not weekly_content.coding_tasks:
        print(f"📝 Getting weekly content for week {week_number}...")
        
        # Try to get from master plan (shared across all candidates for this codebase)
        result = await db.execute(
            select(MasterPlan)
            .where(MasterPlan.codebase_id == learning_plan.codebase_id)
            .order_by(desc(MasterPlan.version))
            .limit(1)
        )
        master_plan = result.scalar_one_or_none()
        
        if master_plan and master_plan.weeks_data:
            print(f"  ✅ Found master plan - copying content from master plan")
            # Find the week in master plan
            week_content = next(
                (w for w in master_plan.weeks_data if w.get("week_number") == week_number),
                None
            )
            
            if week_content:
                # Copy content from master plan
                reading = week_content.get("reading_material", {})
                tasks = week_content.get("coding_tasks", [])
                quiz = week_content.get("quiz", [])
                
                # If we have expectations, ensure we have reasons
                if expectation_context:
                    from app.services.grok_service import grok_service
                    
                    # Generate reasoning for reading if missing
                    if reading and not reading.get("reason"):
                        print("  🧠 Generating reasoning for reading material...")
                        reading["reason"] = await grok_service.generate_reasoning(
                            expectation_context, 
                            "reading material", 
                            reading.get("title", "Weekly Reading"), 
                            reading.get("content", "")[:200]
                        )
                    
                    # Generate reasoning for tasks if missing
                    reasoning_tasks = []
                    for task in tasks:
                        if not task.get("reason"):
                            reasoning_tasks.append(task)
                    
                    if reasoning_tasks:
                        print(f"  🧠 Generating reasoning for {len(reasoning_tasks)} tasks...")
                        # Process in parallel
                        async def update_task_reason(t):
                            t["reason"] = await grok_service.generate_reasoning(
                                expectation_context,
                                "coding task",
                                t.get("title", "Task"),
                                t.get("description", "")[:200]
                            )
                        
                        await asyncio.gather(*[update_task_reason(t) for t in reasoning_tasks])
            else:
                raise HTTPException(status_code=404, detail=f"Week {week_number} not found in master plan")
        else:
            print(f"  ⚠️  No master plan found - generating content on-demand")
            # Fallback: Generate on-demand (for when master plan doesn't exist yet)
            weeks = learning_plan.plan_data.get("weeks", [])
            week_data = next((w for w in weeks if w.get("week_number") == week_number), None)
            
            if not week_data:
                raise HTTPException(status_code=404, detail=f"Week {week_number} not found in learning plan")
            
            # Get codebase analysis for context
            result = await db.execute(
                select(CodebaseAnalysis)
                .where(CodebaseAnalysis.codebase_id == learning_plan.codebase_id)
                .order_by(desc(CodebaseAnalysis.analyzed_at))
                .limit(1)
            )
            analysis_record = result.scalar_one_or_none()
            codebase_analysis = analysis_record.analysis_data if analysis_record else {}
            
            # Generate content using Grok
            from app.services.grok_service import grok_service
            
            print(f"  📚 Generating reading material...")
            reading = await grok_service.generate_weekly_reading(week_data, codebase_analysis, expectation_context)
            
            print(f"  💻 Generating coding tasks...")
            tasks = await grok_service.generate_coding_tasks(week_data, codebase_analysis, expectation_context)
            
            print(f"  📝 Generating quiz...")
            quiz = await grok_service.generate_quiz(week_data, reading.get("content", ""))
        
        # Create or update weekly content
        if weekly_content:
            weekly_content.reading_material = reading
            weekly_content.coding_tasks = tasks
            weekly_content.quiz = quiz
        else:
            weekly_content = WeeklyContent(
                learning_plan_id=learning_plan.id,
                week_number=week_number,
                reading_material=reading,
                coding_tasks=tasks,
                quiz=quiz
            )
            db.add(weekly_content)
        
        await db.commit()
        await db.refresh(weekly_content)
        
        print(f"✅ Weekly content saved for week {week_number}")
    
    # Backfill reasoning if missing (for existing content)
    if weekly_content and expectation_context:
        updated = False
        reading = weekly_content.reading_material
        tasks = weekly_content.coding_tasks
        
        # Check reading
        if reading and not reading.get("reason"):
            print("  🧠 Backfilling reasoning for reading material...")
            from app.services.grok_service import grok_service
            # Create a copy to ensure SQLAlchemy detects change
            new_reading = copy.deepcopy(reading)
            new_reading["reason"] = await grok_service.generate_reasoning(
                expectation_context, 
                "reading material", 
                new_reading.get("title", "Weekly Reading"), 
                new_reading.get("content", "")[:200]
            )
            weekly_content.reading_material = new_reading
            flag_modified(weekly_content, "reading_material")
            updated = True
            
        # Check tasks
        if tasks:
            tasks_updated = False
            reasoning_tasks = []
            
            for i, task in enumerate(tasks):
                if not task.get("reason"):
                    reasoning_tasks.append((i, task))
            
            if reasoning_tasks:
                print(f"  🧠 Backfilling reasoning for {len(reasoning_tasks)} tasks...")
                from app.services.grok_service import grok_service
                
                # Create copy of tasks
                new_tasks = copy.deepcopy(tasks)
                
                async def update_task_backfill(idx, t):
                    t["reason"] = await grok_service.generate_reasoning(
                        expectation_context,
                        "coding task",
                        t.get("title", "Task"),
                        t.get("description", "")[:200]
                    )
                    return idx, t
                
                results = await asyncio.gather(*[update_task_backfill(i, new_tasks[i]) for i, _ in reasoning_tasks])
                
                # Update tasks list
                for idx, t in results:
                    new_tasks[idx] = t
                    
                weekly_content.coding_tasks = new_tasks
                flag_modified(weekly_content, "coding_tasks")
                updated = True

        if updated:
            db.add(weekly_content)
            await db.commit()
            await db.refresh(weekly_content)
            print("  ✅ Reasoning backfilled")

    return WeeklyContentResponse(
        week_number=weekly_content.week_number,
        reading_material=weekly_content.reading_material,
        coding_tasks=weekly_content.coding_tasks,
        quiz=weekly_content.quiz
    )


@router.post("/progress/{candidate_id}")
async def update_progress(
    candidate_id: int,
    progress: ProgressUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update candidate progress"""
    # Get or create progress record
    result = await db.execute(
        select(Progress).where(
            Progress.candidate_id == candidate_id,
            Progress.week_number == progress.week_number
        )
    )
    progress_record = result.scalar_one_or_none()
    
    if not progress_record:
        progress_record = Progress(
            candidate_id=candidate_id,
            week_number=progress.week_number
        )
        db.add(progress_record)
    
    # Update progress
    if progress.reading_completed is not None:
        progress_record.reading_completed = 1 if progress.reading_completed else 0
    
    if progress.task_id is not None:
        tasks = progress_record.tasks_completed or []
        if progress.task_id not in tasks:
            tasks.append(progress.task_id)
        progress_record.tasks_completed = tasks
    
    if progress.quiz_answers is not None:
        progress_record.quiz_answers = progress.quiz_answers
        progress_record.quiz_score = len([a for a in progress.quiz_answers if a is not None])
    
    await db.commit()
    
    return {"message": "Progress updated successfully"}


@router.post("/progress/{candidate_id}/week/{week_number}/chapter/{chapter_number}/complete")
async def mark_chapter_complete(
    candidate_id: int,
    week_number: int,
    chapter_number: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark a chapter as complete"""
    # Get or create progress record
    result = await db.execute(
        select(Progress).where(
            Progress.candidate_id == candidate_id,
            Progress.week_number == week_number
        )
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        progress = Progress(
            candidate_id=candidate_id,
            week_number=week_number,
            reading_completed=[]
        )
        db.add(progress)
    
    # Handle both old integer format and new JSON array format
    if progress.reading_completed is None:
        progress.reading_completed = []
    elif isinstance(progress.reading_completed, int):
        # Convert old integer format to array
        progress.reading_completed = []
    elif not isinstance(progress.reading_completed, list):
        # Ensure it's a list
        progress.reading_completed = []
    
    # Add chapter to completed list if not already there
    if chapter_number not in progress.reading_completed:
        progress.reading_completed.append(chapter_number)
        progress.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Chapter marked as complete",
        "completed_chapters": progress.reading_completed
    }


@router.get("/progress/{candidate_id}/week/{week_number}")
async def get_week_progress(
    candidate_id: int,
    week_number: int,
    db: AsyncSession = Depends(get_db)
):
    """Get progress for a specific week including completed chapters"""
    result = await db.execute(
        select(Progress).where(
            Progress.candidate_id == candidate_id,
            Progress.week_number == week_number
        )
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        return {
            "candidate_id": candidate_id,
            "week_number": week_number,
            "completed_chapters": [],
            "completed_tasks": [],
            "quiz_score": None
        }
    
    return {
        "candidate_id": candidate_id,
        "week_number": week_number,
        "completed_chapters": progress.reading_completed or [],
        "completed_tasks": progress.tasks_completed or [],
        "quiz_score": progress.quiz_score
    }


@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    """List all candidates"""
    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()
    return candidates


@router.get("/candidate/{candidate_id}/status")
async def get_candidate_status(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Check if candidate's resume analysis is complete"""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "id": candidate.id,
        "name": candidate.name,
        "analysis_complete": candidate.resume_analysis is not None,
        "resume_analysis": candidate.resume_analysis
    }


@router.post("/generate-master-plan/{codebase_id}")
async def generate_master_plan_endpoint(codebase_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate comprehensive master plan template for a codebase.
    This should be run once per codebase (admin only in production).
    """
    from app.services.plan_template_service import plan_template_service
    
    try:
        master_plan = await plan_template_service.generate_master_plan(codebase_id, db)
        return {
            "message": "Master plan generated successfully",
            "plan_id": master_plan["id"],
            "weeks_count": len(master_plan["weeks"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Master plan generation failed: {str(e)}")


@router.get("/master-plan/{codebase_id}")
async def get_master_plan_endpoint(codebase_id: str, db: AsyncSession = Depends(get_db)):
    """Get the latest master plan for a codebase"""
    from app.services.plan_template_service import plan_template_service
    
    master_plan = await plan_template_service.get_master_plan(codebase_id, db)
    
    return master_plan


@router.get("/codebase/{codebase_id}/files")
async def get_codebase_files(codebase_id: str, path: str = "", db: AsyncSession = Depends(get_db)):
    """List files in the codebase"""
    from app.services.file_service import file_service
    
    # Ensure repo exists (lazy clone if needed)
    # We need to look up the URL from DB if we want to be 100% correct, 
    # but for optimization we can check if it exists first.
    
    try:
        files = file_service.list_files(codebase_id, path)
        return {"files": files}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/codebase/{codebase_id}/content")
async def get_file_content(codebase_id: str, path: str, db: AsyncSession = Depends(get_db)):
    """Get file content"""
    from app.services.file_service import file_service
    
    # Check if repo exists - if not, we need to clone it. 
    # This might block, so ideally should be done async or beforehand.
    # For now, we assume it's initialized via the Ensure step below.
    
    try:
        content = file_service.get_file_content(codebase_id, path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": content}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
