# 3-Layer Architecture for Skills

## Why This Architecture?

LLMs are probabilistic. Business logic is deterministic. The 3-layer architecture
bridges this gap by separating concerns:

- 90% accuracy per step = 59% success over 5 steps
- Push deterministic complexity into code, keep decisions in the LLM

## The Three Layers

### Layer 1: Directive (The "What")
**In skills**: SKILL.md instructions and reference files

What to do, in what order, with what quality criteria.
Written in natural language Markdown.

Contains:
- Goals and success criteria
- Process steps and decision points
- Quality gates and validation rules
- Edge cases and error handling
- Domain knowledge and thresholds

### Layer 2: Orchestration (The "How")
**In skills**: Claude's reasoning and routing

The intelligent glue between intent and execution.

Responsibilities:
1. Parse user intent
2. Read the relevant skill instructions
3. Plan execution order
4. Call tools and scripts
5. Handle results and errors
6. Learn and adapt

### Layer 3: Execution (The "Do")
**In skills**: Scripts in scripts/

Deterministic code that does reliable, repeatable work.

Properties:
- Same input -> same output
- One script, one responsibility
- Testable independently
- Clear error messages
- Well-documented

## When to Use Each Layer

| Task Type | Layer |
|-----------|-------|
| "Analyze this and tell me what you think" | L1 (directive) + L2 (orchestration) |
| "Parse this HTML and extract all links" | L3 (script) |
| "Decide which workflow to use" | L2 (orchestration) |
| "Validate this YAML frontmatter" | L3 (script) |
| "Generate a report with recommendations" | L1 (directive) + L2 (orchestration) |
| "Calculate a score from these metrics" | L3 (script) if complex formula |

## Rule of Thumb

**Use a script (L3) when:**
- The operation is fragile (XML manipulation, file packaging)
- Exact format matters (ZIP creation, validation)
- Math/calculations are involved
- Same operation happens repeatedly
- Errors would be hard to diagnose

**Use instructions (L1) when:**
- Judgment is required
- Output varies by context
- Creative or analytical work
- Multiple valid approaches exist

## Self-Annealing

When things break:
1. Read the error
2. Diagnose root cause
3. Fix (script if deterministic, instruction if judgment)
4. Test the fix
5. Update the skill with the learning

The system gets stronger with each failure.

## Applying to Skill Design

### Tier 1-2 Skills
- L1: SKILL.md body
- L2: Claude's built-in reasoning
- L3: Optional scripts for fragile ops

### Tier 3-4 Skills
- L1: SKILL.md + sub-skill instructions + reference files
- L2: Orchestrator routing + subagent coordination
- L3: Multiple scripts for validation, processing, analysis

The key insight: Don't try to do everything in instructions.
If something can go wrong, make it a script.
If it requires judgment, keep it in instructions.
