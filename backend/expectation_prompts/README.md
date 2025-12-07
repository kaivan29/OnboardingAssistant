# Analysis Prompts for LLM-Based Onboarding

## Overview

This directory contains prompt templates used by the codebase analysis system to generate experience-level-specific onboarding plans.

## Prompt Files

### `junior_engineer_prompt.md`
**Target Audience:** Junior software engineers (0-3 years experience)

**Focus Areas:**
- Fundamental concepts and domain knowledge
- Essential code entry points for beginners
- Safe, hands-on learning tasks
- Progressive learning: read → understand → modify → implement

**Output Structure:**
1. Required domain knowledge (with explanations of why it matters)
2. Must-study code paths (with file paths and relationships)
3. Ramp-up tasks (3-5 items, sorted by difficulty)
4. Suggested first 2 weeks schedule

---

### `senior_engineer_prompt.md`
**Target Audience:** Senior software engineers (3+ years experience)

**Focus Areas:**
- Architecture-level domain knowledge
- Critical code ownership areas
- High-impact engineering tasks
- Cross-module understanding and system-wide improvements

**Output Structure:**
1. Critical architecture concepts
2. High-priority code areas to master
3. High-impact ramp-up tasks (3-6 items)
4. Roadmap for first 4-6 weeks

## How It Works

### 1. Codebase Analysis Job
The periodic codebase analysis job (`services/codebase_scheduler.py`) reads these prompts and uses them to guide the LLM analysis:

```python
from config_prompts import get_prompt_template

# Get the appropriate prompt
prompt = get_prompt_template("junior")  # or "senior"

# Use this prompt to analyze the codebase
# The LLM will follow the structure defined in the prompt
```

### 2. Experience Level Detection
When a new hire uploads their resume, the system automatically determines their experience level:

```python
from config_prompts import determine_experience_level

profile = {...}  # Analyzed resume data
level = determine_experience_level(profile)  # Returns "junior" or "senior"
```

**Heuristic:** 
- 3+ years of experience → senior
- < 3 years → junior

### 3. Study Plan Generation
The study plan generator (`services/study_plan_generator.py`) uses the experience level to select the appropriate analysis:

```python
# Load codebase analysis
codebase = get_latest_codebase_analysis(repo_url)

# Get experience-specific analysis
if "analyses" in codebase and level in codebase["analyses"]:
    level_analysis = codebase["analyses"][level]
    # Use level-specific chapters, tasks, etc.
```

## Stored Analysis Format

The codebase analysis results are stored with both junior and senior analyses:

```json
{
  "repo_url": "https://github.com/facebook/rocksdb",
  "analyzed_at": "2025-12-07T04:30:00Z",
  "analysis_id": "facebook_rocksdb_20251207_043000",
  "metadata": {
    "repo_name": "facebook_rocksdb",
    "analysis_version": "2.0",
    "includes_prompts": true,
    "experience_levels": ["junior", "senior"]
  },
  "analyses": {
    "junior": {
      "summary": {...},
      "chapters": [...],
      "knowledge_graph": {...}
    },
    "senior": {
      "summary": {...},
      "chapters": [...],
      "knowledge_graph": {...}
    }
  }
}
```

## Configuration

### Repo Configuration (`config_repos.py`)

```python
ANALYSIS_CONFIG = {
    "generate_for_levels": ["junior", "senior"],
    # ... other settings
}
```

### Prompt Configuration (`config_prompts.py`)

```python
PROMPT_TEMPLATES = {
    "junior": "junior_engineer_prompt.md",
    "senior": "senior_engineer_prompt.md"
}
```

## Customization

### Adding a New Experience Level

1. Create a new prompt file (e.g., `intern_prompt.md`)
2. Add it to `config_prompts.py`:
   ```python
   PROMPT_TEMPLATES = {
       "intern": "intern_prompt.md",
       "junior": "junior_engineer_prompt.md",
       "senior": "senior_engineer_prompt.md"
   }
   ```
3. Update `config_repos.py`:
   ```python
   ANALYSIS_CONFIG = {
       "generate_for_levels": ["intern", "junior", "senior"],
   }
   ```
4. Update the `determine_experience_level()` function in `config_prompts.py`

### Modifying Existing Prompts

Simply edit the markdown files in this directory. The changes will be picked up by the next scheduled analysis job.

## Best Practices

1. **Keep prompts focused**: Each prompt should have a clear target audience and purpose
2. **Use structured output**: Define clear output formats to ensure consistent results
3. **Include examples**: Help the LLM understand what kind of content you want
4. **Explain the "why"**: Prompts should ask the LLM to explain why concepts matter, not just what they are
5. **Progressive difficulty**: Junior prompts should emphasize progressive learning paths

## Testing

To test prompt changes manually:

```bash
# Trigger a manual analysis job
curl -X POST http://localhost:8080/api/codebases/trigger

# Check the generated analyses
curl http://localhost:8080/api/codebases
```

## Future Improvements

- [ ] Add prompt versioning to track changes over time
- [ ] Implement prompt A/B testing to optimize effectiveness
- [ ] Add more granular experience levels (intern, mid-level, staff, principal)
- [ ] Include domain-specific prompts (e.g., ML engineer vs. backend engineer)
- [ ] Add prompt validation to ensure they follow best practices
