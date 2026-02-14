# Writing Effective Skill Descriptions

The description field is the single most important part of your skill. It determines
when Claude activates your skill. Get this right.

## The Framework

Every description needs three components:

```
[WHAT] + [CAPABILITIES] + [WHEN/TRIGGERS]
```

### Component 1: WHAT (capability statement)
One sentence explaining the skill's core purpose.

### Component 2: CAPABILITIES (detailed features)
Key capabilities and domains covered.

### Component 3: WHEN (trigger phrases)
Explicit phrases users would say, prefixed with "Use when user says" or "Triggers on:".

## Examples: Good vs Bad

### Example 1: SEO Skill

**Bad:**
```
description: Helps with SEO.
```
Problems: Too vague, no triggers, Claude won't know when to activate.

**Good:**
```
description: >
  Comprehensive SEO analysis for any website. Performs full site audits,
  single-page analysis, technical SEO checks, schema markup detection,
  content quality assessment, and sitemap analysis. Triggers on: "SEO",
  "audit", "schema", "Core Web Vitals", "sitemap", "E-E-A-T",
  "technical SEO", "content quality", "page speed", "structured data".
```

### Example 2: Code Review Skill

**Bad:**
```
description: Reviews code and suggests improvements.
```
Problems: Too generic, overlaps with Claude's built-in ability.

**Good:**
```
description: >
  Automated code review following team conventions and security best
  practices. Checks code style, complexity metrics, security vulnerabilities
  (OWASP Top 10), test coverage gaps, and documentation quality. Use when
  user says "code review", "review this PR", "check for security issues",
  "code quality audit", or "review my changes".
```

### Example 3: Data Pipeline Skill

**Bad:**
```
description: Processes data pipelines and ETL workflows.
```
Problems: No trigger phrases, missing key capabilities.

**Good:**
```
description: >
  Design, validate, and troubleshoot data pipelines and ETL workflows.
  Covers schema validation, data quality checks, pipeline orchestration
  (Airflow, Prefect, Dagster), transformation logic, and monitoring setup.
  Use when user says "data pipeline", "ETL", "data quality", "schema
  validation", "Airflow DAG", "data transformation", or "pipeline monitoring".
```

## Trigger Phrase Strategy

### Include Multiple Formulations
Users say things differently. Cover:
- Formal: "perform SEO analysis"
- Casual: "check my site's SEO"
- Action-oriented: "audit this website"
- Domain-specific: "Core Web Vitals", "schema markup"

### Include Tool/Technology Names
If your skill relates to specific tools:
- "Kubernetes", "Docker", "Terraform"
- "React", "Next.js", "Tailwind"
- "PostgreSQL", "Redis", "MongoDB"

### Include File Types (if relevant)
- "PDF", "CSV", "JSON", "YAML"
- ".py files", ".tsx components"

### Add Negative Triggers (if over-triggering risk)
```
Do NOT use for simple code formatting or syntax questions.
Not intended for general-purpose data analysis.
```

## Length Guidelines

| Skill Type | Description Length |
|-----------|-------------------|
| Simple skill | 100-200 characters |
| Domain skill | 200-500 characters |
| Multi-skill orchestrator | 500-900 characters |
| Maximum allowed | 1024 characters |

## Testing Your Description

After writing, test with these questions:
1. Would Claude activate for "help me [primary use case]"? -> Should be YES
2. Would Claude activate for "[specific trigger phrase]"? -> Should be YES
3. Would Claude activate for "help me with [unrelated task]"? -> Should be NO
4. Is the description specific enough to distinguish from similar skills?
5. Does it mention domain keywords that users would actually say?

## The "When Would You Use This?" Test

Ask Claude: "When would you use the [skill-name] skill?"

Claude will quote the description back. If Claude's answer doesn't match your
intended use cases, revise the description.

## Common Pitfalls

1. **Too vague**: "Helps with projects" -- activate on EVERYTHING
2. **Too narrow**: "Processes Q4 2024 sales data" -- almost never activates
3. **Missing triggers**: Good explanation but no "use when" phrases
4. **Jargon only**: Technical terms without lay equivalents
5. **No capabilities**: Triggers without explaining what the skill does
6. **Over 1024 chars**: Will be rejected by the system
