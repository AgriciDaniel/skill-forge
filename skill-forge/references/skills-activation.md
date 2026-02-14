# Skill Discovery & Activation Reference

How Claude Code finds, loads, and activates skills. Critical knowledge for
writing descriptions that trigger correctly.

## Skill Locations (Priority Order)

1. **Enterprise** (highest priority)
2. **Personal**: `~/.claude/skills/*/SKILL.md`
3. **Project**: `.claude/skills/*/SKILL.md`
4. **Additional directories**: via `--add-dir` (auto-loaded)
5. **Plugin**: `skills/*/SKILL.md` within installed plugins
6. **Nested**: Auto-discovered from `.claude/skills` in subdirectories (monorepo)

## How Activation Works

1. **Metadata always loaded**: Name + description always in context (~100 words each)
2. **Character budget**: 2% of context window (override: `SLASH_COMMAND_TOOL_CHAR_BUDGET`)
3. **SKILL.md body**: Loaded when skill triggers (<5k words recommended)
4. **Resources**: Loaded on-demand by Claude (unlimited via scripts)

**Activation triggers:**
- User invokes via `/skill-name` or `/skill-name args`
- Claude auto-invokes when description matches user's intent
- Recently/frequently used skills get priority
- Skills without extra permissions allowed without approval

## Complete Skill Frontmatter

```yaml
---
# Required
name: kebab-case-name            # 1-64 chars, must match folder
description: >                   # 1-1024 chars, determines activation
  This skill should be used when...

# Optional - UI/Invocation
argument-hint: "[target]"        # Placeholder shown in UI
disable-model-invocation: false  # Prevent Claude auto-invoking
user-invocable: true             # Show in slash command menu

# Optional - Permissions
allowed-tools:                   # Pre-approved tools
  - Read
  - Write
  - Bash(npm:*)

# Optional - Execution
model: inherit                   # sonnet | opus | haiku | inherit
context: fork                    # Run in isolated subagent
agent: custom-agent-name         # Delegate to specific agent

# Optional - Hooks (scoped to skill lifecycle)
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: prompt
          prompt: "Validate"
          once: true

# Optional - Metadata
license: MIT
compatibility: "Requires Python 3.10+"
metadata:
  author: YourName
  version: 1.0.0
---
```

## String Substitutions in Skills

| Substitution | Description |
|-------------|-------------|
| `$ARGUMENTS` | All arguments passed to the skill |
| `$ARGUMENTS[0]`, `$ARGUMENTS[1]` | Individual arguments |
| `$0`, `$1`, `$2` | Positional shorthand |
| `${CLAUDE_SESSION_ID}` | Current session UUID |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin root directory |

## Dynamic Context Injection

Execute bash at skill load time with `!` backtick syntax:

```markdown
Current branch: !`git branch --show-current`
Recent commits: !`git log --oneline -5`
```

Output injected into skill content before sending to Claude.

## Context Fork

```yaml
context: fork
```

Runs skill in isolated subagent context. Prevents heavy tool usage from
polluting the main conversation. Useful for exploration-heavy skills.

## Permission Model

### Permission Levels (Priority Order)
1. Managed policy (organization-enforced, highest)
2. User settings: `~/.claude/settings.json`
3. Project settings: `.claude/settings.json`
4. Local settings: `.claude/settings.local.json`
5. Skill frontmatter: `allowed-tools`

### Permission Decisions
| Decision | Effect |
|----------|--------|
| `allow` | Tool executes without prompting |
| `deny` | Tool blocked entirely |
| `ask` | User prompted for approval |

### allowed-tools Behavior
- Pre-approves listed tools when skill is active
- Supports YAML list or JSON array format
- `${CLAUDE_PLUGIN_ROOT}` substituted in plugin context
- `"*"` grants access to ALL tools

## Skill Hot-Reload

Skills created or modified in `~/.claude/skills` or `.claude/skills` are
immediately available without restarting the session.

## Hidden Features for Skill Creators

### Automatic Continue
When response hits output token limit, Claude automatically continues.
Skills generating long output benefit from this.

### Large Bash Output
Large command outputs saved to disk with file path reference (not truncated).
Skills can run commands with arbitrarily large output.

### Skill Character Budget Scaling
Budget scales with context window (2% of context). Larger context = more
skill descriptions visible without truncation.

### Plan Mode
`/plan` command enters plan mode. Shift+Tab selects "auto-accept edits".

### Subagent Transcripts
Stored at `~/.claude/projects/{project}/{sessionId}/subagents/`.
Useful for debugging or chaining workflows.

### File References
- `@path/to/file` includes file inline in prompts
- `@` autocomplete shows icons for different file types
