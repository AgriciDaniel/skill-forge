# Hooks System Reference

Hooks execute shell commands, LLM prompts, or agents in response to Claude Code events.
Use hooks to enforce quality gates, validate outputs, and automate workflows.

## All 15 Hook Events

| Event | Trigger | Matcher | Key Capability |
|-------|---------|---------|---------------|
| `PreToolUse` | Before tool executes | Tool name | approve/deny/modify input |
| `PostToolUse` | After tool succeeds | Tool name | inject feedback, suppress output |
| `PostToolUseFailure` | After tool fails | Tool name | handle failures |
| `Stop` | Before Claude stops | Stop reason | block until quality met |
| `SubagentStop` | Before subagent stops | Stop reason | validate subagent work |
| `SubagentStart` | Subagent launches | Agent type | inject context |
| `SessionStart` | Session begins | `*` | set up environment |
| `SessionEnd` | Session ends | `*` | cleanup |
| `UserPromptSubmit` | User submits prompt | `*` | modify/validate input |
| `PreCompact` | Before compaction | `*` | inject extra context |
| `Notification` | Notification sent | `*` | log/forward |
| `PermissionRequest` | Permission asked | Tool name | intercept prompts |
| `Setup` | Via `--init`/`--maintenance` | `*` | first-run setup |
| `TeammateIdle` | Agent team member idle | Agent type | assign work |
| `TaskCompleted` | Delegated task done | Agent type | react to results |

## Hook Types

### Command Hook (type: "command")
```json
{
  "type": "command",
  "command": "bash scripts/validate.sh",
  "timeout": 30
}
```
- Receives JSON via stdin with event data
- Exit 0 = success, Exit 2 = blocking error, other = warning
- stdout parsed as JSON, stderr shown on exit code 2

### Prompt Hook (type: "prompt")
```json
{
  "type": "prompt",
  "prompt": "Analyze: $TOOL_INPUT. Return 'approve' or 'deny'.",
  "timeout": 15
}
```
- LLM evaluates the prompt with event context
- Can reference `$TOOL_INPUT`, `$TOOL_INPUT.field_name`, `$TRANSCRIPT_PATH`

### Agent Hook (type: "agent")
```json
{
  "type": "agent",
  "prompt": "Review the code changes and verify quality.",
  "timeout": 60
}
```
- Spawns a subagent with tool access
- Most powerful but most expensive

## Configuration Locations

1. `~/.claude/settings.json` -- user-level
2. `.claude/settings.json` -- project-level (team-shared)
3. `.claude/settings.local.json` -- project-level (personal)
4. Plugin `hooks/hooks.json`
5. Skill/agent YAML frontmatter `hooks` field

## Matcher Patterns

| Pattern | Example | Matches |
|---------|---------|---------|
| Exact | `Write` | Only Write tool |
| Pipe-separated | `Write\|Edit` | Write or Edit |
| Wildcard | `*` | Everything |
| Regex | `mcp__.*__delete.*` | MCP delete operations |

## Hook Output Formats

### Standard Output
```json
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Additional context for Claude"
}
```

### PreToolUse Decision
```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "updatedInput": {"command": "modified command"},
    "additionalContext": "Extra context"
  }
}
```
Decisions: `allow`, `deny`, `ask`

### Stop/SubagentStop Decision
```json
{"decision": "approve"}
```
or
```json
{"decision": "block", "reason": "Tests not run"}
```

## Environment Variables in Hooks

| Variable | Available In |
|----------|-------------|
| `$CLAUDE_PROJECT_DIR` | All hooks |
| `$CLAUDE_PLUGIN_ROOT` | Plugin hooks |
| `$CLAUDE_ENV_FILE` | SessionStart only |
| `$TRANSCRIPT_PATH` | Prompt hooks |
| `$TOOL_INPUT` | Prompt hooks (PreToolUse) |

## Hooks in Skill/Agent Frontmatter

```yaml
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: prompt
          prompt: "Validate write"
          once: true
  Stop:
    - matcher: "*"
      hooks:
        - type: command
          command: "bash scripts/check-quality.sh"
```

Special flags:
- `once: true` -- execute only once per activation
- `async: true` -- run in background
- Hooks for same event run in parallel
- Skill hooks scoped to skill lifecycle only

## Common Patterns for Skill Creators

### Quality Gate (block Stop until tests pass)
```yaml
hooks:
  Stop:
    - matcher: "*"
      hooks:
        - type: command
          command: "bash scripts/run-tests.sh"
```

### Validate Tool Input (pre-approve with modification)
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: prompt
          prompt: "Is this command safe? $TOOL_INPUT"
```

### Post-Write Linting
```yaml
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "bash scripts/lint.sh"
```
