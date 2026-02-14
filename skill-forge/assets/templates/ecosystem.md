# Template: Full Ecosystem (Tier 4)

Use for enterprise-grade skills with parallel subagent delegation, multiple scripts,
industry templates, and comprehensive reference knowledge.

## Structure
```
skill-name/                  # Main orchestrator
  SKILL.md
  references/
    ref-1.md
    ref-2.md
    ref-3.md
  assets/
    template-a.md
    template-b.md
  scripts/
    fetch_data.py
    parse_data.py
    validate.py
skills/
  skill-name-audit/          # Full audit with parallel delegation
    SKILL.md
  skill-name-sub1/
    SKILL.md
  skill-name-sub2/
    SKILL.md
  skill-name-sub3/
    SKILL.md
  ...
agents/
  skill-name-role1.md
  skill-name-role2.md
  skill-name-role3.md
install.sh
```

## Main Orchestrator Template

Same as Tier 3 multi-skill template, PLUS:

```markdown
## Subagents

For parallel analysis during full audits:
- `skill-name-role1` -- {{RESPONSIBILITY}}
- `skill-name-role2` -- {{RESPONSIBILITY}}
- `skill-name-role3` -- {{RESPONSIBILITY}}

## Industry Templates

Available in `assets/`:
- `assets/template-a.md` -- for {{INDUSTRY_A}}
- `assets/template-b.md` -- for {{INDUSTRY_B}}
```

## Audit Sub-Skill Template (with parallel delegation)

```markdown
---
name: {{PARENT}}-audit
description: >
  Full {{DOMAIN}} audit with parallel subagent delegation. {{CAPABILITIES}}.
  Use when user says "audit", "full check", "analyze", or "health check".
---

# Full {{DOMAIN}} Audit

## Process

### Step 1: Gather Input
Collect URL/data from user.

### Step 2: Initial Analysis
Run: `python scripts/fetch_data.py {{INPUT}}`

### Step 3: Detect Context
Identify industry/type from initial data.

### Step 4: Parallel Delegation
Spawn subagents in parallel:

| Agent | Responsibility | Reference Files |
|-------|---------------|-----------------|
| {{PARENT}}-role1 | {{TASK}} | `references/{{REF}}.md` |
| {{PARENT}}-role2 | {{TASK}} | `references/{{REF}}.md` |
| {{PARENT}}-role3 | {{TASK}} | `references/{{REF}}.md` |

(If subagents unavailable, run inline sequentially)

### Step 5: Aggregate Results
Collect all agent outputs.
Calculate aggregate health score (0-100).

### Step 6: Generate Report

## Output: FULL-AUDIT-REPORT.md

```markdown
# {{DOMAIN}} Audit Report

**URL**: {{URL}}
**Date**: {{DATE}}
**Health Score**: {{SCORE}}/100

## Executive Summary
{{2-3 SENTENCES}}

## Scores by Category
| Category | Score | Status |
|----------|-------|--------|
| {{CAT_1}} | {{SCORE}} | {{EMOJI}} |
| {{CAT_2}} | {{SCORE}} | {{EMOJI}} |
| {{CAT_3}} | {{SCORE}} | {{EMOJI}} |

## Critical Issues
{{PRIORITIZED_LIST}}

## Action Plan
### Immediate (This Week)
{{ITEMS}}

### Short-Term (This Month)
{{ITEMS}}

### Long-Term (This Quarter)
{{ITEMS}}
```
```

## Agent Definition Template

Agents use YAML frontmatter (different from skills). Body becomes system prompt.

```markdown
---
name: {{PARENT}}-{{ROLE}}
description: >
  {{WHAT_THIS_AGENT_ANALYZES}}. Scores {{CATEGORY}} on a 0-100 scale.
  <example>User says: "{{EXAMPLE_TRIGGER}}"</example>
  <example>User says: "{{EXAMPLE_TRIGGER}}"</example>
model: inherit
color: {{blue|cyan|green|yellow|magenta|red}}
tools:
  - Read
  - Grep
  - Glob
---

You are a {{ROLE}} specialist.

## Your Role

{{WHAT_THIS_AGENT_ANALYZES_IN_THE_PARALLEL_WORKFLOW}}

## Process

1. Receive {{INPUT_DATA}} from the orchestrating audit skill
2. {{ANALYSIS_STEP_1}}
3. {{ANALYSIS_STEP_2}}
4. Score each item on a 0-10 scale
5. Calculate category score (0-100)

## Scoring Criteria

| Check | Weight | Pass | Fail |
|-------|--------|------|------|
| {{CHECK_1}} | {{WEIGHT}} | {{CRITERIA}} | {{CRITERIA}} |

## Output Format

Return structured markdown with score, findings table, and recommendations.

## Cross-References

- Load `references/{{REF}}.md` for {{DOMAIN_KNOWLEDGE}}
- Defer detailed {{TOPIC}} analysis to `{{PARENT}}-{{OTHER_SUB}}` sub-skill
```

## Industry Template File

```markdown
# {{INDUSTRY}} Template

## Overview
Key characteristics of {{INDUSTRY}} for this domain.

## Industry-Specific Checks
| Check | Importance | Details |
|-------|-----------|---------|
| {{CHECK_1}} | Critical | {{EXPLANATION}} |
| {{CHECK_2}} | High | {{EXPLANATION}} |

## Benchmarks
| Metric | Good | Average | Poor |
|--------|------|---------|------|
| {{METRIC_1}} | {{VALUE}} | {{VALUE}} | {{VALUE}} |

## Recommendations
{{INDUSTRY_SPECIFIC_RECOMMENDATIONS}}
```

## Checklist
- [ ] Main orchestrator under 150 lines
- [ ] Each sub-skill under 200 lines
- [ ] Agents have YAML frontmatter (name, description, model, tools)
- [ ] Agent descriptions use `<example>` blocks
- [ ] Scoring methodology defined with weights
- [ ] Industry templates cover target verticals
- [ ] Scripts for all deterministic operations
- [ ] install.sh tested (install + uninstall)
- [ ] Parallel delegation with sequential fallback
- [ ] Shared references (no duplication)
- [ ] Priority levels defined (Critical/High/Medium/Low)
