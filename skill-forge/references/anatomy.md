# Skill Anatomy & Structure

## The Only Required File: SKILL.md

Every skill is a folder containing at minimum a `SKILL.md` file. Everything else is optional.

## SKILL.md Format

```markdown
---
name: skill-name
description: >
  What it does. When to use it. Keywords for matching.
---

# Skill Title

[Instructions in Markdown]
```

### Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|------------|
| `name` | Yes | 1-64 chars, kebab-case, must match folder name |
| `description` | Yes | 1-1024 chars, no XML tags, must include WHAT + WHEN |
| `argument-hint` | No | Placeholder shown in UI (e.g., `[url]`) |
| `disable-model-invocation` | No | If `true`, only user can invoke (not Claude) |
| `user-invocable` | No | If `false`, hidden from slash command menu |
| `allowed-tools` | No | List of pre-approved tools (e.g., Read, Bash, WebFetch) |
| `model` | No | `sonnet`, `opus`, `haiku`, `inherit` |
| `context` | No | `fork` runs skill in isolated subagent |
| `agent` | No | Delegate to specific agent type |
| `hooks` | No | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |
| `license` | No | License name or reference to LICENSE.txt |
| `compatibility` | No | 1-500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value pairs (author, version, etc.) |

### Body Content

No format restrictions on the body. Write whatever helps accomplish the task.

**Size targets:**
- Under 500 lines
- Under 5000 tokens
- Move detailed content to references/

## Directory Structure

```
skill-name/                    # Required: kebab-case folder
  SKILL.md                     # Required: exact case
  scripts/                     # Optional: executable code
    process.py
    validate.sh
  references/                  # Optional: on-demand documentation
    domain-guide.md
    api-reference.md
  assets/                      # Optional: templates, data files
    template.md
    config.json
```

## Progressive Disclosure (3 Levels)

### Level 1: Metadata (Always Loaded)
- `name` + `description` from YAML frontmatter
- Injected into system prompt at startup
- ~50-100 tokens per skill
- Used to decide WHEN to activate

### Level 2: Instructions (Loaded on Activation)
- Full SKILL.md body content
- Loaded when task matches description
- Target: <5000 tokens
- Core workflow instructions

### Level 3: Resources (Loaded on Demand)
- Files in scripts/, references/, assets/
- Loaded only when explicitly referenced during execution
- No size limit (but keep individual files focused)

## Multi-Skill Architecture

### Main Orchestrator
```
skill-name/SKILL.md
```
- Routes commands to sub-skills
- Contains shared configuration (scoring, quality gates)
- References shared knowledge in its own references/

### Sub-Skills
```
skills/skill-name-sub1/SKILL.md
skills/skill-name-sub2/SKILL.md
```
- One focused workflow each
- Can run independently OR be orchestrated
- Cross-reference shared refs via relative paths

### Agents (for parallel delegation)
```
agents/skill-name-role1.md
agents/skill-name-role2.md
```
- Subagent definitions for parallel execution
- Each has a clear role, input, and output format
- Used by audit/analysis sub-skills

**Agent frontmatter format** (different from skills):

| Field | Required | Constraints |
|-------|----------|------------|
| `name` | Yes | 3-50 chars, kebab-case |
| `description` | Yes | CAN use `<example>` blocks (unlike skills) |
| `model` | No | `inherit`, `sonnet`, `opus`, `haiku` |
| `color` | No | `blue`, `cyan`, `green`, `yellow`, `magenta`, `red` |
| `tools` | No | List of allowed tools (inherits all if omitted) |
| `disallowedTools` | No | Explicitly denied tools |
| `permissionMode` | No | `default`, `acceptEdits`, `delegate`, `dontAsk`, `plan` |
| `maxTurns` | No | Maximum conversation turns |
| `skills` | No | Skills available to the agent |
| `hooks` | No | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |
| `memory` | No | `user`, `project`, or `local` scope |

Body after `---` becomes the agent's system prompt (write in second person).

### Scripts (deterministic execution)
```
scripts/script_name.py
```
- One script, one responsibility
- CLI interface with structured JSON output
- Error handling and validation built in

## File Naming Rules

| Type | Convention | Example |
|------|-----------|---------|
| Skill folder | kebab-case | `my-skill` |
| Sub-skill folder | `parent-child` | `my-skill-audit` |
| SKILL.md | Exact case | `SKILL.md` (never `skill.md`) |
| Scripts | snake_case | `fetch_data.py` |
| References | kebab-case | `api-guide.md` |
| Agents | `parent-role.md` | `my-skill-analyzer.md` |

## What NOT to Include

- No `README.md` inside skill folders (use repo-level README)
- No `.env` or credential files
- No `node_modules/` or `__pycache__/`
- No `claude` or `anthropic` in skill names
- No XML angle brackets in frontmatter
