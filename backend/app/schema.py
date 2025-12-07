from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any


# Request Schemas
class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    resume_text: str


class CodebaseAnalyzeRequest(BaseModel):
    codebase_url: str
    github_token: Optional[str] = None


class LearningPlanCreate(BaseModel):
    candidate_id: int
    codebase_url: str
    github_token: Optional[str] = None
    force_regenerate: Optional[bool] = False  # Skip cache and regenerate plan


# Response Schemas
class ResumeAnalysis(BaseModel):
    background: str
    skills: List[str]
    experience_level: str
    strengths: List[str]
    learning_areas: List[str]
    ramp_up_expectation: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    resume_analysis: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class WeeklyReadingMaterial(BaseModel):
    title: str
    content: str
    key_concepts: List[str]
    resources: List[str]
    reason: Optional[str] = None


class CodingTask(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    estimated_time: str
    files_to_modify: List[str]
    hints: List[str]
    reason: Optional[str] = None


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: int
    explanation: str


class WeeklyContentResponse(BaseModel):
    week_number: int
    reading_material: WeeklyReadingMaterial
    coding_tasks: List[CodingTask]
    quiz: List[QuizQuestion]


class WeekPlan(BaseModel):
    week_number: int
    title: str
    objectives: List[str]
    topics: List[str]


class LearningPlanResponse(BaseModel):
    id: int
    candidate_id: int
    codebase_url: str
    weeks: List[WeekPlan]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    week_number: int
    reading_completed: Optional[bool] = None
    task_id: Optional[str] = None
    quiz_answers: Optional[List[int]] = None
