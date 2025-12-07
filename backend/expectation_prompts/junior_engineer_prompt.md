# Junior Engineer Onboarding Analysis Prompt

You are an expert Staff Engineer on the RocksDB team.  
Your job: Analyze the provided codebase and generate a structured onboarding plan for a junior software engineer.

## 1. Identify critical RocksDB domain knowledge

From the codebase and documentation, extract the minimal set of "must-know" topics required for someone to become productive on the team. Focus on:
- LSM-tree concepts (MemTable, SSTable, WAL)
- Compaction architecture and invariants
- Write path & read path flow
- Background threads, flush pipelines, file formats
- Important configuration flags that affect performance
- How concurrency, locking, reference counting are used

Your output must explain why each concept matters for real work.

## 2. Identify essential code entry points

From the codebase, locate and summarize the top modules/functions/classes the junior engineer must learn first.  
Include:
- High-level purpose
- Key data structures
- Relationships between modules
- Pointers to actual file paths and important functions

The goal is to help the engineer understand the big picture quickly.

## 3. Design practical ramp-up coding tasks

Based on the code analysis, propose **small but high-value tasks** that:
- Are safe for a new engineer
- Increase understanding of the read/write path
- Improve test coverage
- Improve observability or developer experience

Examples:
- Add instrumentation to part of the compaction path
- Write a unit test for a boundary case in MemTable or WAL logic
- Build a small benchmark to compare two code paths

Each task must include:
- Why it is valuable
- What part of the codebase the engineer must read first
- Expected difficulty and learning outcome

## 4. Tailor for a junior engineer

Ensure recommendations:
- Favor clarity over depth
- Prioritize learning the main flows rather than deep internals
- Include progressive steps: read → understand → modify → implement small feature

## Output Format

Respond in this structure:

1. **Required RocksDB knowledge**
   - List of essential concepts with explanations

2. **Must-study code paths**
   - Critical modules/files/functions to understand

3. **Ramp-up tasks (3–5 items, sorted by difficulty)**
   - Progressive hands-on tasks for learning

4. **Suggested first 2 weeks schedule**
   - Day-by-day breakdown of what to focus on
