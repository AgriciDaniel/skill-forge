# Template: Minimal Skill (Tier 1)

Use this template for simple, single-file skills that don't need scripts or sub-skills.

## Structure
```
skill-name/
  SKILL.md
```

## Template

```markdown
---
name: {{SKILL_NAME}}
description: >
  {{WHAT_IT_DOES}}. {{DETAILED_CAPABILITIES}}.
  Use when user says "{{TRIGGER_1}}", "{{TRIGGER_2}}",
  "{{TRIGGER_3}}", or "{{TRIGGER_4}}".
---

# {{SKILL_TITLE}}

{{ONE_LINE_OVERVIEW}}

## Instructions

### Step 1: {{FIRST_STEP_NAME}}
{{CLEAR_EXPLANATION}}

Expected outcome: {{WHAT_SUCCESS_LOOKS_LIKE}}

### Step 2: {{SECOND_STEP_NAME}}
{{CLEAR_EXPLANATION}}

### Step 3: {{THIRD_STEP_NAME}}
{{CLEAR_EXPLANATION}}

## Examples

### Example 1: {{COMMON_SCENARIO}}
User says: "{{EXAMPLE_INPUT}}"

Actions:
1. {{ACTION_1}}
2. {{ACTION_2}}

Result: {{EXPECTED_OUTPUT}}

### Example 2: {{ANOTHER_SCENARIO}}
User says: "{{EXAMPLE_INPUT}}"

Result: {{EXPECTED_OUTPUT}}

## Troubleshooting

### Error: {{COMMON_ERROR}}
**Cause:** {{WHY_IT_HAPPENS}}
**Solution:** {{HOW_TO_FIX}}

### Error: {{ANOTHER_ERROR}}
**Cause:** {{WHY_IT_HAPPENS}}
**Solution:** {{HOW_TO_FIX}}
```

## Checklist
- [ ] Description has WHAT + WHEN + keywords
- [ ] Instructions are specific (not "do it properly")
- [ ] At least 2 examples provided
- [ ] At least 1 troubleshooting entry
- [ ] Under 200 lines
