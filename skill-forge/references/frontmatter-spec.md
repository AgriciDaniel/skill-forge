# YAML Frontmatter Specification

## Format

```yaml
---
name: skill-name
description: >
  Description text here.
---
```

The `---` delimiters are required. Frontmatter must be at the very top of SKILL.md.

## Required Fields

### name

| Property | Requirement |
|----------|------------|
| Type | String |
| Length | 1-64 characters |
| Format | kebab-case (lowercase letters, numbers, hyphens) |
| Restrictions | No leading, trailing, or consecutive hyphens |
| Must match | Parent directory name exactly |
| Reserved | Cannot contain "claude" or "anthropic" |

**Valid examples:**
```
name: seo-audit
name: data-pipeline
name: frontend-design
name: my-skill-v2
```

**Invalid examples:**
```
name: SEO Audit         # spaces and capitals
name: seo_audit         # underscores
name: -seo-audit        # leading hyphen
name: seo--audit        # consecutive hyphens
name: claude-helper     # reserved word "claude"
```

### description

| Property | Requirement |
|----------|------------|
| Type | String |
| Length | 1-1024 characters |
| Must include | WHAT it does + WHEN to use it |
| Forbidden | XML angle brackets (< >) |
| Recommended | 5-10 trigger phrases |

**Structure framework:**
```
[Capability statement]. [Detailed capabilities]. Use when user says
"[trigger 1]", "[trigger 2]", "[trigger 3]", or "[trigger 4]".
```

**YAML multiline options:**

Folded scalar (recommended for long descriptions):
```yaml
description: >
  First line continues
  on the next line as one paragraph.
  Use when user says "trigger".
```

Literal scalar (preserves newlines):
```yaml
description: |
  Line one.
  Line two.
  Line three.
```

Quoted string:
```yaml
description: "Short description. Use when user says trigger."
```

## Optional Fields

### argument-hint
```yaml
argument-hint: "[url] [options]"
```
Placeholder text shown in the UI when the skill appears in the slash command menu.
Helps users understand what arguments the skill expects.

### disable-model-invocation
```yaml
disable-model-invocation: true
```
Boolean. If `true`, only the user can invoke this skill via `/skill-name`.
Claude cannot auto-invoke it based on description matching. Default: `false`.

### user-invocable
```yaml
user-invocable: false
```
Boolean. If `false`, the skill is hidden from the slash command menu.
Useful for sub-skills that should only be invoked by a parent orchestrator. Default: `true`.

### allowed-tools
```yaml
allowed-tools:
  - Read
  - Bash
  - WebFetch
  - Glob
  - Grep
```
Pre-approved tools the skill can use without additional permission.
Supports patterns like `Bash(git:*)` for restricted bash access.
Use `"*"` to grant access to all tools (use sparingly).

### model
```yaml
model: sonnet
```
Override the model used when this skill executes.
Valid values: `sonnet`, `opus`, `haiku`, `inherit`. Default: inherits from session.

### context
```yaml
context: fork
```
Runs the skill in an isolated subagent context, preventing heavy tool usage
from polluting the main conversation. Useful for skills that do extensive exploration.

### agent
```yaml
agent: custom-agent-name
```
Delegate skill execution to a specific agent type defined in `agents/`.

### hooks
```yaml
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: prompt
          prompt: "Validate the write operation"
          once: true
```
Hook definitions scoped to this skill's lifecycle. Supported events:
`PreToolUse`, `PostToolUse`, `Stop`. The `once: true` flag makes a hook
execute only once per skill activation.

### license
```yaml
license: MIT
# or
license: Complete terms in LICENSE.txt
```

### compatibility
```yaml
compatibility: "Requires Claude Code with Bash tool access. Needs Python 3.10+ and Node.js 18+."
```
1-500 characters. Indicates environment requirements.

### metadata
```yaml
metadata:
  author: YourName
  version: 1.0.0
  mcp-server: your-service
```
Arbitrary string key-value pairs.

## Common Mistakes

| Mistake | Wrong | Correct |
|---------|-------|---------|
| Missing delimiters | `name: my-skill` (no `---`) | Wrap in `---` delimiters |
| Unclosed quotes | `description: "Does things` | `description: "Does things"` |
| XML tags | `description: Creates <div>` | `description: Creates HTML div` |
| Invalid name | `name: My Skill` | `name: my-skill` |
| Spaces in name | `name: my skill` | `name: my-skill` |

## Validation

Run: `python scripts/validate_skill.py /path/to/skill`

Checklist: `---` present, name is kebab-case matching folder, description
under 1024 chars with no `<` or `>`, optional fields follow constraints.
