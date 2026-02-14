# Template: Workflow Skill (Tier 2)

Use for skills that need deterministic scripts alongside instructions.

## Structure
```
skill-name/
  SKILL.md
  scripts/
    validate.py
    process.py
  references/
    domain-guide.md
```

## Template

```markdown
---
name: {{SKILL_NAME}}
description: >
  {{WHAT_IT_DOES}}. {{DETAILED_CAPABILITIES}}.
  Use when user says "{{TRIGGER_1}}", "{{TRIGGER_2}}",
  "{{TRIGGER_3}}", "{{TRIGGER_4}}", or "{{TRIGGER_5}}".
allowed-tools:
  - Read
  - Bash
  - WebFetch
---

# {{SKILL_TITLE}}

{{ONE_LINE_OVERVIEW}}

## Process

### Step 1: {{GATHER_INPUTS}}
{{WHAT_TO_COLLECT_FROM_USER}}

Validate inputs before proceeding:
- {{VALIDATION_RULE_1}}
- {{VALIDATION_RULE_2}}

### Step 2: {{EXECUTE}}
Run the processing script:
```bash
python scripts/process.py {{INPUT_ARGS}}
```

Expected output: {{DESCRIBE_OUTPUT_FORMAT}}

### Step 3: {{VALIDATE_RESULTS}}
Run validation:
```bash
python scripts/validate.py {{OUTPUT_ARGS}}
```

If validation fails:
- {{ERROR_1}}: {{RECOVERY_ACTION_1}}
- {{ERROR_2}}: {{RECOVERY_ACTION_2}}

### Step 4: {{DELIVER}}
{{HOW_TO_PRESENT_RESULTS}}

## Quality Gates

Before delivering output:
- [ ] {{CHECK_1}}
- [ ] {{CHECK_2}}
- [ ] {{CHECK_3}}

## Reference Files

Load on-demand as needed:
- `references/domain-guide.md` -- {{WHAT_IT_CONTAINS}}

## Examples

### Example 1: {{SCENARIO}}
Input: {{INPUT}}
Script output: {{OUTPUT}}
Final result: {{DELIVERED_RESULT}}

## Troubleshooting

### Script fails with {{ERROR}}
**Cause:** {{REASON}}
**Solution:** {{FIX}}
```

## Checklist
- [ ] Scripts have docstrings and CLI interface
- [ ] Scripts output structured JSON
- [ ] Validation gates between steps
- [ ] Error handling with recovery paths
- [ ] References linked, not inlined
- [ ] Under 300 lines in SKILL.md
