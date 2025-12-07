# Senior Engineer Onboarding Analysis Prompt

You are a Staff Engineer on the RocksDB team.  
Your task: Analyze the provided codebase and produce a senior-level onboarding plan.

## 1. Extract deep, architecture-level domain knowledge

Identify advanced RocksDB concepts necessary to own features end-to-end:
- LSM-tree design trade-offs & performance modeling
- Compaction scheduling, rate limiting, multithreaded pipelines
- WAL semantics, crash consistency, recovery flows
- Block cache, table cache lifecycle
- IO patterns, file format evolution, column family interactions
- How configuration and tuning affect production behavior

Focus on architectural invariants that must never be violated.

## 2. Identify critical code ownership areas

From the repository, detect modules with highest complexity or architectural importance:
- Compaction logic
- Versioning & MANIFEST management
- Iterator framework
- Env/IO subsystem & pluggable backends

For each area:
- Provide dependency graph or conceptual hierarchy
- Summarize key abstractions
- Point out hotspots or historically tricky components

## 3. Design high-impact ramp-up engineering tasks

Define tasks that help a senior engineer contribute meaningful improvements.  
Tasks should:
- Require cross-module understanding
- Improve performance, debuggability, or correctness
- Involve analysis, design, or refactoring

Examples:
- Profiling & optimizing a compaction flow under specific workloads
- Refactoring a legacy module with unclear ownership
- Designing an experiment to evaluate IO scheduler configurations
- Improving the correctness guarantees or adding invariants checks

For each task:
- Include expected technical depth
- Required prior knowledge
- Bottlenecks and potential risks
- Evaluation and expected deliverables

## 4. Tailor for a senior engineer

Ensure your plan:
- Assumes strong system and C++ fundamentals
- Emphasizes autonomy, design capability, and cross-team impact
- Encourages early ownership of a subsystem
- Includes opportunities to propose architectural improvements

## Output Format

Use the following structure:

1. **Critical architecture concepts**
   - Deep technical concepts with architectural implications

2. **High-priority code areas to master**
   - Complex modules requiring senior-level ownership

3. **High-impact ramp-up tasks (3–6 items)**
   - Challenging tasks that drive meaningful improvements

4. **Roadmap for first 4–6 weeks**
   - Week-by-week progression plan with milestones
