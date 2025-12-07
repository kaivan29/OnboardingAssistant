import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import get_db, Progress, WeeklyContent, LearningPlan
from sqlalchemy import select, desc

async def main():
    # Context manager for get_db
    db_gen = get_db()
    session = await db_gen.__anext__()
    
    try:
        candidate_id = 2
        week_num = 1
        
        print(f"Checking Progress for Candidate {candidate_id}, Week {week_num}")
        
        # Get Plan
        result = await session.execute(
            select(LearningPlan)
            .where(LearningPlan.candidate_id == candidate_id)
            .order_by(desc(LearningPlan.created_at))
            .limit(1)
        )
        plan = result.scalars().first()
        if not plan:
            print("No plan found!")
            return
        print(f"Plan ID: {plan.id}")
        
        # Get Content
        result = await session.execute(
            select(WeeklyContent).where(
                WeeklyContent.learning_plan_id == plan.id,
                WeeklyContent.week_number == week_num
            ).limit(1)
        )
        content = result.scalars().first()
        
        if not content:
            print("No content found!")
            return
            
        # Get Progress
        result = await session.execute(
            select(Progress).where(
                Progress.candidate_id == candidate_id,
                Progress.week_number == week_num
            ).limit(1)
        )
        progress = result.scalars().first()
        
        if not progress:
            print("No progress found!")
            return
        
        # Reading Analysis
        reading_text = content.reading_material.get("content", "")
        sections = reading_text.count("## ")
        import math
        total_chapters = max(1, math.ceil(sections / 2)) if sections > 0 else 1
        
        completed_chapters = len(progress.reading_completed) if isinstance(progress.reading_completed, list) else 0
        
        print(f"\n--- READING ---")
        print(f"Sections (H2): {sections}")
        print(f"Estimated Chapters: {total_chapters}")
        print(f"Completed Chapters: {completed_chapters} {progress.reading_completed}")
        reading_score = min(1.0, completed_chapters / total_chapters)
        print(f"Score: {reading_score:.2f} (x30 = {reading_score*30:.1f})")
        
        # Tasks Analysis
        total_tasks = len(content.coding_tasks or [])
        completed_tasks = len(progress.tasks_completed) if progress.tasks_completed else 0
        
        print(f"\n--- TASKS ---")
        print(f"Total Tasks: {total_tasks}")
        print(f"Completed Tasks: {completed_tasks} {progress.tasks_completed}")
        tasks_score = min(1.0, completed_tasks / total_tasks) if total_tasks else 0
        print(f"Score: {tasks_score:.2f} (x40 = {tasks_score*40:.1f})")
        
        # Quiz Analysis
        total_quiz = len(content.quiz or [])
        quiz_score_val = progress.quiz_score or 0
        
        print(f"\n--- QUIZ ---")
        print(f"Total Questions: {total_quiz}")
        print(f"Quiz Score Val (DB): {quiz_score_val}")
        print(f"Quiz Answers (DB): {progress.quiz_answers}")
        quiz_score = min(1.0, quiz_score_val / total_quiz) if total_quiz else 0
        print(f"Score: {quiz_score:.2f} (x30 = {quiz_score*30:.1f})")
        
        week_percent = (reading_score * 30) + (tasks_score * 40) + (quiz_score * 30)
        print(f"\nTOTAL SCORE: {week_percent}")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
