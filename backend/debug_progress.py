
import asyncio
import sys
import math
from app.database import get_db, Candidate, Progress, WeeklyContent, LearningPlan
from sqlalchemy import select, desc
from app.services.file_service import file_service

async def check_progress(candidate_id=1):
    async for db in get_db():
        print(f"--- Checking Progress for Candidate {candidate_id} ---")
        
        # Get Candidate
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            print("Candidate not found")
            return

        print(f"Candidate: {candidate.name}")

        # Get Learning Plan
        result = await db.execute(select(LearningPlan)
                                .where(LearningPlan.candidate_id == candidate_id)
                                .order_by(desc(LearningPlan.created_at))
                                .limit(1))
        plan = result.scalar_one_or_none()
        if not plan:
            print("No Learning Plan found")
            return
            
        weeks = plan.plan_data.get("weeks", [])
        print(f"Total Weeks in Plan: {len(weeks)}")

        total_percent = 0
        
        for week in weeks:
            week_num = week['week_number']
            print(f"\nWeek {week_num}:")
            
            # Get Content
            result = await db.execute(select(WeeklyContent).where(
                WeeklyContent.learning_plan_id == plan.id, 
                WeeklyContent.week_number == week_num
            ))
            content = result.scalar_one_or_none()
            
            # Get Progress
            result = await db.execute(select(Progress).where(
                Progress.candidate_id == candidate_id, 
                Progress.week_number == week_num
            ))
            progress = result.scalar_one_or_none()
            
            if not content:
                print("  No WeeklyContent found -> 0%")
                continue
                
            if not progress:
                print("  No Progress record found -> 0%")
                continue
                
            # Reading
            reading_text = content.reading_material.get("content", "")
            sections = reading_text.count("## ")
            # estimated_chapters logic from backend
            total_chapters = max(1, math.ceil(sections / 2)) if sections > 0 else 1
            completed_chapters = len(progress.reading_completed) if isinstance(progress.reading_completed, list) else 0
            
            print(f"  Reading: Completed {completed_chapters} / {total_chapters} chapters. (Raw list: {progress.reading_completed})")
            reading_score = min(1.0, completed_chapters / total_chapters)
            
            # Tasks
            total_tasks = len(content.coding_tasks)
            completed_tasks = len(progress.tasks_completed) if progress.tasks_completed else 0
            print(f"  Tasks: Completed {completed_tasks} / {total_tasks} tasks. (Raw list: {progress.tasks_completed})")
            tasks_score = 0
            if total_tasks > 0:
                tasks_score = min(1.0, completed_tasks / total_tasks)

            # Quiz
            total_quiz = len(content.quiz)
            quiz_score_val = progress.quiz_score or 0
            print(f"  Quiz: Score {quiz_score_val} / {total_quiz} questions.")
            quiz_score = 0
            if total_quiz > 0:
                quiz_score = min(1.0, quiz_score_val / total_quiz)
                
            week_p = (reading_score * 30) + (tasks_score * 40) + (quiz_score * 30)
            print(f"  Week Score: {week_p:.2f}%")
            total_percent += week_p
            
        total_weeks = len(weeks)
        if total_weeks > 0:
            overall = round(total_percent / total_weeks)
            print(f"\nOverall Progress: {overall}%")
        else:
            print("\nOverall Progress: 0% (No weeks)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cid = int(sys.argv[1])
    else:
        cid = 1
    asyncio.run(check_progress(cid))
