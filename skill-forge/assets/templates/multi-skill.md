# Template: Multi-Skill Orchestrator (Tier 3)

Use for complex domains with multiple distinct workflows routed from a main skill.

## Structure
```
skill-name/                  # Main orchestrator
  SKILL.md
  references/
    shared-ref-1.md
    shared-ref-2.md
  scripts/
    shared_script.py
skills/
  skill-name-sub1/
    SKILL.md
  skill-name-sub2/
    SKILL.md
  skill-name-sub3/
    SKILL.md
```

## Main Orchestrator Template

```markdown
---
name: {{SKILL_NAME}}
description: >
  {{COMPREHENSIVE_DESCRIPTION_OF_ENTIRE_DOMAIN}}.
  {{LIST_KEY_CAPABILITIES}}.
  Triggers on: "{{KEYWORD_1}}", "{{KEYWORD_2}}", "{{KEYWORD_3}}",
  "{{KEYWORD_4}}", "{{KEYWORD_5}}", "{{KEYWORD_6}}".
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# {{SKILL_TITLE}} -- {{TAGLINE}}

{{ONE_LINE_OVERVIEW}}

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/{{NAME}}` | Interactive mode |
| `/{{NAME}} {{SUB1}}` | {{SUB1_DESCRIPTION}} |
| `/{{NAME}} {{SUB2}}` | {{SUB2_DESCRIPTION}} |
| `/{{NAME}} {{SUB3}}` | {{SUB3_DESCRIPTION}} |

## Orchestration Logic

When user invokes `/{{NAME}}`:
1. Parse command to identify sub-skill
2. If specific command, route to sub-skill directly
3. If no command, enter interactive mode:
   - Ask what user wants to accomplish
   - Detect context/industry type
   - Route to appropriate sub-skill

## Context Detection

Detect context type from user input:
- **Type A**: {{SIGNALS}} -> route to {{SUB_SKILL}}
- **Type B**: {{SIGNALS}} -> route to {{SUB_SKILL}}
- **Type C**: {{SIGNALS}} -> route to {{SUB_SKILL}}

## Quality Gates

{{DOMAIN_SPECIFIC_HARD_RULES}}

## Scoring Methodology (if applicable)

### Health Score (0-100)
| Category | Weight |
|----------|--------|
| {{CAT_1}} | {{WEIGHT}}% |
| {{CAT_2}} | {{WEIGHT}}% |
| {{CAT_3}} | {{WEIGHT}}% |

## Reference Files

Load on-demand:
- `references/{{REF_1}}.md` -- {{DESCRIPTION}}
- `references/{{REF_2}}.md` -- {{DESCRIPTION}}

## Sub-Skills

1. **{{NAME}}-{{SUB1}}** -- {{DESCRIPTION}}
2. **{{NAME}}-{{SUB2}}** -- {{DESCRIPTION}}
3. **{{NAME}}-{{SUB3}}** -- {{DESCRIPTION}}
```

## Sub-Skill Template

```markdown
---
name: {{PARENT}}-{{CHILD}}
description: >
  {{FOCUSED_DESCRIPTION}}.
  Use when user says "{{TRIGGER_1}}", "{{TRIGGER_2}}",
  "{{TRIGGER_3}}", or "{{TRIGGER_4}}".
---

# {{CHILD_TITLE}}

## Process

### Step 1: {{ACTION}}
{{INSTRUCTIONS}}

### Step 2: {{ACTION}}
{{INSTRUCTIONS}}

## Output Format

{{DEFINE_STRUCTURED_OUTPUT}}

## Cross-References

- For {{RELATED_TOPIC}}, see `{{PARENT}}-{{OTHER_CHILD}}` sub-skill
- Load `references/{{REF}}.md` for {{KNOWLEDGE}}
```

## Checklist
- [ ] Main orchestrator has routing table
- [ ] Each sub-skill has focused responsibility
- [ ] Naming follows parent-child convention
- [ ] Shared knowledge in parent references/
- [ ] No duplicated content across sub-skills
- [ ] Main SKILL.md under 150 lines
- [ ] Sub-skills under 200 lines each
