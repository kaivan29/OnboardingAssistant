import httpx
import json
from typing import Dict, Any, List, Optional
from app.config import get_settings

settings = get_settings()


class GrokService:
    """Service for interacting with Grok API"""
    
    def __init__(self):
        self.api_key = settings.xai_api_key
        self.base_url = settings.xai_base_url
        self.model = settings.xai_model
        self.resume_model = settings.xai_resume_model  # Cheaper model for resume analysis
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, messages: List[Dict[str, str]], temperature: float = 0.7, model: str = None) -> str:
        """Make a request to Grok API"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            }
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from Grok response with robust error handling"""
        import re
        
        # Try direct parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            # Try to find JSON object in response
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError(f"Could not parse JSON from response: {response[:200]}")
        
        # Clean the string
        json_str = json_str.strip()
        
        # Try parsing
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Last resort: try to fix common JSON errors
            json_str = json_str.replace("\n", " ").replace("\r", "")
            return json.loads(json_str)
    
    async def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """Analyze resume to understand candidate background"""
        prompt = f"""Analyze this resume and provide a structured assessment:

Resume:
{resume_text}

Provide analysis in JSON format with the following structure:
{{
    "background": "Brief summary of candidate's background",
    "skills": ["skill1", "skill2", ...],
    "experience_level": "junior|mid|senior",
    "strengths": ["strength1", "strength2", ...],
    "learning_areas": ["area1", "area2", ...]
}}

Focus on technical skills, experience level, and areas where the candidate could benefit from additional learning."""

        messages = [
            {"role": "system", "content": "You are an expert technical recruiter and career advisor. Analyze resumes thoroughly and provide actionable insights."},
            {"role": "user", "content": prompt}
        ]
        
        # Use cheaper model for resume analysis
        response = await self._make_request(messages, temperature=0.3, model=self.resume_model)
        
        # Extract JSON from response
        try:
            # Try to parse as JSON directly
            analysis = json.loads(response)
        except json.JSONDecodeError:
            # If not pure JSON, try to extract JSON from markdown code block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            else:
                raise ValueError("Could not parse JSON from Grok response")

        # Generate Ramp Up Expectation based on level
        try:
            level = analysis.get("experience_level", "junior").lower()
            if "senior" in level or "staff" in level or "lead" in level:
                prompt_file = "senior_engineer_prompt.md"
            else:
                prompt_file = "junior_engineer_prompt.md"

            from pathlib import Path
            # Assuming running from backend root or app root
            # Try to find the file relative to current file or project root
            base_path = Path(__file__).parent.parent.parent / "expectation_prompts"
            prompt_path = base_path / prompt_file
            
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    expectation_context = f.read()

                exp_prompt = f"""Based on the candidate's analysis and the following onboarding philosophy, write a concise (2-3 sentences) "Ramp Up Expectation" message to the candidate.
                
                Candidate Background: {analysis.get('background')}
                Experience Level: {level}
                
                Onboarding Philosophy:
                {expectation_context}
                
                The message should set the tone for their first 4 weeks, highlighting what matters most (e.g., specific deep dives for seniors vs. practical tasks for juniors).
                Directly address the candidate ("You will focus on..."). keep it under 50 words."""

                exp_messages = [
                    {"role": "system", "content": "You are a thoughtful engineering manager setting expectations for a new hire."},
                    {"role": "user", "content": exp_prompt}
                ]

                expectation_text = await self._make_request(exp_messages, temperature=0.5, model=self.resume_model)
                analysis["ramp_up_expectation"] = expectation_text.strip()
            else:
                print(f"Warning: Expectation prompt file not found at {prompt_path}")
                analysis["ramp_up_expectation"] = "Welcome to the team! We are excited to have you onboard and look forward to seeing your contributions."

        except Exception as e:
            print(f"Error generating expectation: {e}")
            analysis["ramp_up_expectation"] = "Welcome to the team! We look forward to your ramp up."
        
        return analysis
    
    async def analyze_codebase(self, codebase_url: str, github_token: Optional[str] = None) -> Dict[str, Any]:
        """Analyze codebase structure and dependencies using Grok"""
        prompt = f"""Analyze this codebase repository: {codebase_url}

Provide a comprehensive analysis in JSON format:
{{
    "tech_stack": ["technology1", "technology2", ...],
    "architecture": "Brief description of the architecture",
    "main_components": [
        {{"name": "component1", "description": "...", "complexity": "low|medium|high"}},
        ...
    ],
    "dependencies": ["dependency1", "dependency2", ...],
    "key_patterns": ["pattern1", "pattern2", ...],
    "recommended_learning_path": ["topic1", "topic2", ...]
}}

Focus on understanding the codebase structure to help create a learning plan for new hires."""

        messages = [
            {"role": "system", "content": "You are an expert software architect who specializes in onboarding new team members. Analyze codebases to create effective learning paths."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.3)
        
        # Extract JSON from response
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            else:
                raise ValueError("Could not parse JSON from Grok response")
        
        return analysis
    
    async def generate_learning_plan(
        self, 
        resume_analysis: Dict[str, Any], 
        codebase_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate 4-week personalized learning plan"""
        prompt = f"""Create a personalized 4-week onboarding learning plan for a new hire.

Candidate Profile:
{json.dumps(resume_analysis, indent=2)}

Codebase Analysis:
{json.dumps(codebase_analysis, indent=2)}

Generate a comprehensive 4-week plan in JSON format:
{{
    "overview": "Brief overview of the learning journey",
    "weeks": [
        {{
            "week_number": 1,
            "title": "Week 1 title",
            "objectives": ["objective1", "objective2", ...],
            "topics": ["topic1", "topic2", ...],
            "focus_areas": ["area1", "area2", ...]
        }},
        ... (for all 4 weeks)
    ]
}}

The plan should:
- Start with fundamentals and gradually increase complexity
- Align with the candidate's experience level
- Cover the main components and patterns of the codebase
- Include both theoretical knowledge and practical coding
- Be realistic and achievable within 4 weeks"""

        messages = [
            {"role": "system", "content": "You are an expert technical mentor who designs effective onboarding programs. Create structured, personalized learning plans."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.5)
        
        # Extract JSON from response
        try:
            plan = json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                plan = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                plan = json.loads(json_str)
                raise ValueError("Could not parse JSON from Grok response")
        
        return plan
    
    async def generate_reasoning(
        self,
        expectation_context: str,
        item_type: str,
        item_title: str,
        item_description: str
    ) -> str:
        """Generate a short reason for why this item was assigned based on expectations"""
        prompt = f"""Explain why this {item_type} is relevant for the candidate based on these expectations:

Expectations:
{expectation_context}

Item: {item_title}
Description: {item_description}

Provide a ONE SENTENCE reason (under 30 words) starting with "Relevant because..." or "This helps you..."."""

        messages = [
            {"role": "system", "content": "You are a mentor explaining the 'why' behind a learning plan."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.7, model=self.resume_model)
        return response.strip()

    async def generate_weekly_reading(
        self,
        week_plan: Dict[str, Any],
        codebase_analysis: Dict[str, Any],
        expectation_context: str = None
    ) -> Dict[str, Any]:
        """Generate AI-powered wiki-style reading material for a week"""
        reason_prompt = ""
        if expectation_context:
            reason_prompt = f"""
Expectation Context:
{expectation_context}

Also, add a "reason" field to the JSON explaining why this reading is relevant to the expectation."""

        prompt = f"""Create comprehensive reading material for this week of the onboarding plan:

Week Plan:
{json.dumps(week_plan, indent=2)}

Codebase Context:
{json.dumps(codebase_analysis, indent=2)}
{reason_prompt}

Generate detailed reading material in JSON format:
{{
    "title": "Week title",
    "content": "Comprehensive wiki-style content in markdown format covering all topics. Include code examples, diagrams (as ASCII), and explanations. Make it 1500-2000 words.",
    "key_concepts": ["concept1", "concept2", ...],
    "resources": ["resource1 with URL", "resource2 with URL", ...],
    "reason": "One sentence explaining relevance to the expectation"
}}

IMPORTANT: Return ONLY valid JSON, no markdown code blocks or extra text.
Make the content educational, engaging, and specific to the codebase."""

        messages = [
            {"role": "system", "content": "You are an expert technical writer who creates clear, comprehensive documentation for developers. Write engaging educational content. ALWAYS return valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.6)
        
        # Clean and parse response
        return self._parse_json_response(response)
    
    async def generate_coding_tasks(
        self,
        week_plan: Dict[str, Any],
        codebase_analysis: Dict[str, Any],
        expectation_context: str = None
    ) -> List[Dict[str, Any]]:
        """Generate coding tasks for the week"""
        reason_prompt = ""
        if expectation_context:
            reason_prompt = f"""
Expectation Context:
{expectation_context}

For EACH task, add a "reason" field explaining why it is relevant to the expectation."""

        prompt = f"""Create 3-5 coding tasks for this week of the onboarding plan:

Week Plan:
{json.dumps(week_plan, indent=2)}

Codebase Context:
{json.dumps(codebase_analysis, indent=2)}
{reason_prompt}

Generate tasks in JSON format:
{{
    "tasks": [
        {{
            "id": "task-1",
            "title": "Task title",
            "description": "Detailed description of what to implement",
            "difficulty": "easy|medium|hard",
            "estimated_time": "30 mins - 2 hours",
            "files_to_modify": ["file1.py", "file2.js"],
            "hints": ["hint1", "hint2", ...],
            "reason": "Relevance to expectation"
        }},
        ...
    ]
}}

Tasks should:
- Be practical and related to the actual codebase
- Progressively increase in difficulty
- Help reinforce the week's learning objectives
- Be achievable with the knowledge gained"""

        messages = [
            {"role": "system", "content": "You are an expert coding instructor who designs hands-on programming exercises. Create practical, educational tasks."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.6)
        
        try:
            result = json.loads(response)
            return result.get("tasks", [])
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
                return result.get("tasks", [])
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
                return result.get("tasks", [])
            else:
                try:
                     # Parse using parse_json_response just in case
                    result = self._parse_json_response(response)
                    return result.get("tasks", [])
                except:
                     raise ValueError("Could not parse JSON from Grok response")
    
    async def generate_quiz(
        self,
        week_plan: Dict[str, Any],
        reading_content: str
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions for the week"""
        prompt = f"""Create a quiz with 8-10 multiple choice questions based on this week's content:

Week Plan:
{json.dumps(week_plan, indent=2)}

Reading Content (first 1000 chars):
{reading_content[:1000]}...

Generate quiz in JSON format:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }},
        ...
    ]
}}

Questions should:
- Test understanding of key concepts
- Include some practical application questions
- Have clear, unambiguous correct answers
- Provide helpful explanations"""

        messages = [
            {"role": "system", "content": "You are an expert educator who creates effective assessments. Design quiz questions that test understanding, not just memorization."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.5)
        
        try:
            result = json.loads(response)
            return result.get("questions", [])
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
                return result.get("questions", [])
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
                return result.get("questions", [])
            else:
                raise ValueError("Could not parse JSON from Grok response")


# Singleton instance
grok_service = GrokService()
