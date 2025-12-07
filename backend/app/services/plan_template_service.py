"""
Service for managing master plan templates.

This service handles pre-generation of comprehensive learning plans for codebases
and quick personalization based on candidate profiles.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import MasterPlan, CodebaseAnalysis
from app.services.grok_service import grok_service


class PlanTemplateService:
    """Manages master plan templates for fast personalization"""
    
    async def generate_master_plan(
        self,
        codebase_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive master plan for a codebase.
        This is done once per codebase and stored for reuse.
        """
        # Get latest codebase analysis
        result = await db.execute(
            select(CodebaseAnalysis)
            .where(CodebaseAnalysis.codebase_id == codebase_id)
            .order_by(desc(CodebaseAnalysis.analyzed_at))
            .limit(1)
        )
        analysis_record = result.scalar_one_or_none()
        
        if not analysis_record:
            raise ValueError(f"No codebase analysis found for {codebase_id}")
        
        codebase_analysis = analysis_record.analysis_data
        
        # Generate comprehensive 4-week plan
        print(f"🔧 Generating master plan for {codebase_id}...")
        plan_data = await self._generate_comprehensive_plan(codebase_analysis)
        
        # Generate all weekly content
        weeks_with_content = []
        for week in plan_data.get("weeks", []):
            week_number = week["week_number"]
            print(f"  📚 Generating content for week {week_number}...")
            
            # Generate reading, tasks, and quiz
            reading = await grok_service.generate_weekly_reading(week, codebase_analysis)
            tasks = await grok_service.generate_coding_tasks(week, codebase_analysis)
            quiz = await grok_service.generate_quiz(week, reading.get("content", ""))
            
            week_with_content = {
                **week,
                "reading_material": reading,
                "coding_tasks": tasks,
                "quiz": quiz
            }
            weeks_with_content.append(week_with_content)
        
        # Create master plan record
        master_plan_id = f"{codebase_id}_v1"
        master_plan = MasterPlan(
            id=master_plan_id,
            codebase_id=codebase_id,
            version=1,
            plan_overview=plan_data.get("overview", ""),
            weeks_data=weeks_with_content
        )
        
        db.add(master_plan)
        await db.commit()
        
        print(f"✅ Master plan generated and saved: {master_plan_id}")
        
        return {
            "id": master_plan_id,
            "overview": plan_data.get("overview"),
            "weeks": weeks_with_content
        }
    
    async def _generate_comprehensive_plan(
        self,
        codebase_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a generic 4-week plan for a codebase"""
        prompt = f"""Create a comprehensive 4-week onboarding plan for new hires joining a codebase project.

Codebase Analysis:
{json.dumps(codebase_analysis, indent=2)}

Generate a detailed 4-week curriculum in JSON format:
{{
    "overview": "Brief overview of the learning journey (2-3 sentences)",
    "weeks": [
        {{
            "week_number": 1,
            "title": "Week 1: Foundations and Setup",
            "description": "What the new hire will learn this week",
            "objectives": ["objective1", "objective2", ...],
            "topics": ["topic1", "topic2", ...],
            "focus_areas": ["area1", "area2", ...]
        }},
        ... (for all 4 weeks)
    ]
}}

The plan should:
- Week 1: Environment setup, basic concepts, architecture overview
- Week 2: Core components and data structures
- Week 3: Advanced features and integrations
- Week 4: Performance, testing, and best practices
- Be generic enough to work for most new hires
- Progressive difficulty from beginner to intermediate
- Include both theory and hands-on coding
"""
        
        messages = [
            {"role": "system", "content": "You are an expert technical mentor who designs comprehensive onboarding programs. Create structured, detailed learning plans."},
            {"role": "user", "content": prompt}
        ]
        
        response = await grok_service._make_request(messages, temperature=0.5)
        
        # Parse JSON response
        try:
            plan = json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                plan = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                plan = json.loads(json_str)
            else:
                raise ValueError("Could not parse JSON from Grok response")
        
        return plan
    
    async def get_master_plan(
        self,
        codebase_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the latest master plan for a codebase"""
        result = await db.execute(
            select(MasterPlan)
            .where(MasterPlan.codebase_id == codebase_id)
            .order_by(desc(MasterPlan.version))
            .limit(1)
        )
        master_plan = result.scalar_one_or_none()
        
        if not master_plan:
            return None
        
        return {
            "id": master_plan.id,
            "codebase_id": master_plan.codebase_id,
            "version": master_plan.version,
            "overview": master_plan.plan_overview,
            "weeks": master_plan.weeks_data,
            "generated_at": master_plan.generated_at.isoformat()
        }
    
    async def personalize_plan(
        self,
        master_plan: Dict[str, Any],
        resume_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quickly personalize a master plan based on candidate's resume.
        This is much faster than generating a plan from scratch.
        """
        prompt = f"""Personalize this learning plan for a specific candidate.

Master Plan Overview:
{master_plan.get('overview', '')}

Candidate Profile:
{json.dumps(resume_analysis, indent=2)}

Week Titles:
{json.dumps([{'week': w['week_number'], 'title': w['title']} for w in master_plan.get('weeks', [])], indent=2)}

Based on the candidate's experience level ({resume_analysis.get('experience_level', 'mid')}), skills, and learning areas, provide:

1. Personalized objectives for each week (adjust difficulty and focus)
2. Recommended emphasis areas based on their background
3. Any topics they can skip or accelerate through
4. Specific focus areas for their knowledge gaps

Return JSON:
{{
    "personalized_overview": "Brief personalized intro (2 sentences)",
    "recommendations": ["recommendation1", "recommendation2", ...],
    "week_adjustments": [
        {{
            "week_number": 1,
            "difficulty": "beginner|intermediate|advanced",
            "emphasis": ["area1", "area2"],
            "skip_topics": ["topic1"],
            "additional_focus": ["area1"]
        }},
        ...
    ]
}}

Keep it concise - just the key personalizations."""
        
        messages = [
            {"role": "system", "content": "You are an expert mentor who personalizes learning plans. Be concise and focus on meaningful adjustments."},
            {"role": "user", "content": prompt}
        ]
        
        response = await grok_service._make_request(messages, temperature=0.3, model=grok_service.resume_model)
        
        # Parse response
        try:
            personalizations = json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                personalizations = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                personalizations = json.loads(json_str)
            else:
                # If parsing fails, return master plan as-is
                personalizations = {"personalized_overview": master_plan.get("overview")}
        
        # Apply personalizations to master plan
        personalized_weeks = []
        week_adjustments = {adj["week_number"]: adj for adj in personalizations.get("week_adjustments", [])}
        
        for week in master_plan.get("weeks", []):
            personalized_week = week.copy()
            week_num = week["week_number"]
            
            if week_num in week_adjustments:
                adj = week_adjustments[week_num]
                # Add personalization metadata
                personalized_week["difficulty"] = adj.get("difficulty", "intermediate")
                personalized_week["emphasis"] = adj.get("emphasis", [])
                personalized_week["additional_focus"] = adj.get("additional_focus", [])
            
            personalized_weeks.append(personalized_week)
        
        return {
            "overview": personalizations.get("personalized_overview", master_plan.get("overview")),
            "recommendations": personalizations.get("recommendations", []),
            "weeks": personalized_weeks
        }


# Singleton instance
plan_template_service = PlanTemplateService()
