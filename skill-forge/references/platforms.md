# Multi-Platform Skill Conversion Reference

Platform-specific paths, formats, and compatibility rules for converting Claude Code
skills to OpenAI Codex, Google Gemini CLI, Google Antigravity, and Cursor.

## Skill Storage Paths

| Platform | Project-Level | User-Level (Global) |
|----------|--------------|---------------------|
| Claude Code | `.claude/skills/{name}/` | `~/.claude/skills/{name}/` |
| OpenAI Codex | `.agents/skills/{name}/` | `~/.agents/skills/{name}/` |
| Gemini CLI | `.gemini/skills/{name}/` | `~/.gemini/skills/{name}/` |
| Antigravity | `.agent/skills/{name}/` | `~/.gemini/antigravity/skills/{name}/` |
| Cursor | `.cursor/skills/{name}/` | `~/.cursor/skills/{name}/` |

All platforms use the same `SKILL.md` file as the entry point (Agent Skills standard).

## Project Instruction Files

Each platform has a project-level instruction file that acts like a system prompt:

| Platform | File | Max Size | Hierarchy |
|----------|------|----------|-----------|
| Claude Code | `CLAUDE.md` | ~32 KiB | Root + parent dirs + CWD |
| OpenAI Codex | `AGENTS.md` | ~32 KiB | Root to CWD (hierarchical) |
| Gemini CLI | `GEMINI.md` | ~32 KiB | Project root |
| Antigravity | `GEMINI.md` | ~32 KiB | Workspace root |
| Cursor | `.cursor/rules/*.mdc` | ~32 KiB | Project root |

**Cursor notes**: Rules use `.mdc` extension with a 3-field YAML frontmatter
(`description`, `globs`, `alwaysApply`). Cursor v2.4+ also reads SKILL.md natively.

**Codex notes**: Supports `AGENTS.override.md` per-directory overrides. Configurable
fallback filenames via `project_doc_fallback_filenames` in config.toml.

**Gemini notes**: Configurable filename via `settings.json` -> `context.fileName` array.
Can natively read AGENTS.md from Codex projects.

## Frontmatter Field Compatibility

### Portable Fields (keep on all platforms)

| Field | Notes |
|-------|-------|
| `name` | Required everywhere (optional on Antigravity, defaults to dirname) |
| `description` | Required everywhere; determines activation |
| `license` | Standard field, universally supported |
| `compatibility` | Environment requirements, universally supported |
| `metadata` | Arbitrary key-value pairs, universally supported |

### Adaptable Fields (platform-specific handling)

| Field | Codex | Gemini | Antigravity | Cursor |
|-------|-------|--------|-------------|--------|
| `allowed-tools` | Keep (supported) | Strip + warn | Strip + warn | Strip + warn |
| `disable-model-invocation` | Move to `openai.yaml` | Strip + warn | Strip + warn | Strip + warn |
| `argument-hint` | Keep | Keep | Keep | Keep |

### Claude-Only Fields (strip with warning)

These fields are Claude Code specific and must be removed for other platforms:

- `context` (fork/isolated subagent mode)
- `agent` (delegate to agent type)
- `hooks` (PreToolUse, PostToolUse, Stop lifecycle)
- `model` (sonnet, opus, haiku, inherit)
- `user-invocable` (slash command visibility)
- `skills` (sub-skill references)
- `memory` (persistent memory paths)

**Warning template**: `"Field '{field}' is Claude Code specific and was removed. {workaround}"`

**Codex note**: Codex parses ONLY `name` and `description`; all other fields are silently
ignored. This means adaptable fields like `allowed-tools` are supported in spec but
effectively ignored by the parser.

## Cursor Rule File Format

Cursor rules (`.cursor/rules/*.mdc`) use a minimal 3-field frontmatter:

```yaml
---
description: "When to activate this rule"
globs: "*.ts,src/**/*.tsx"
alwaysApply: false
---

Rule content in markdown...
```

| Field | Type | Notes |
|-------|------|-------|
| `description` | string | Optional; used by agent for relevance matching |
| `globs` | string | File patterns; triggers when matching files are in chat |
| `alwaysApply` | boolean | If true, always loaded; globs are IGNORED when true |

**Quirk**: If both `alwaysApply: true` AND `globs` are set, globs are ignored.

## Codex Platform Extension: openai.yaml

Codex supports an optional `agents/openai.yaml` file for platform-specific config:

```yaml
interface:
  display_name: "Skill Display Name"

policy:
  # Maps from disable-model-invocation
  allow_implicit_invocation: true
```

### Field Mapping to openai.yaml

| Claude Field | openai.yaml Location | Transform |
|-------------|---------------------|-----------|
| `name` | `interface.display_name` | Title case the kebab-case name |
| `disable-model-invocation` | `policy.allow_implicit_invocation` | Invert boolean |

## MCP Configuration Formats

### Claude Code (.mcp.json)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "mcp-server"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### Codex (config.toml)
```toml
[mcp_servers.server-name]
type = "stdio"
command = "npx"
args = ["-y", "mcp-server"]

[mcp_servers.server-name.env]
API_KEY = "..."
```

### Gemini CLI (settings.json)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "mcp-server"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### Antigravity (mcp_config.json)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "mcp-server"]
    }
  }
}
```

### Cursor (mcp.json)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "mcp-server"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

**Key differences**: Codex uses TOML with `[mcp_servers]` section. All others use JSON
with `mcpServers` key. Cursor's format is identical to Claude's.

## Antigravity Template Variables

Antigravity supports template variables in skill instructions:
- `{{SKILL_PATH}}` -- resolves to the skill's directory path
- `{{WORKSPACE_PATH}}` -- resolves to the workspace root

When converting, replace hardcoded relative paths (e.g., `./scripts/`) with
`{{SKILL_PATH}}/scripts/` for portability.

## Hook System Comparison

| Aspect | Claude Code | Codex | Gemini/Antigravity | Cursor |
|--------|------------|-------|-------------------|--------|
| **Event count** | 13 | 1 (notify) | Partial (CLI) | 6 (beta) |
| **Blocking** | Yes (exit 2) | No | No | Yes (allow/deny/ask) |
| **Async support** | Yes (v2.1) | No | No | No |
| **Skill-scoped** | Yes (v2.1) | No | No | No |
| **Config file** | settings.json | config.toml | settings.json | hooks.json |

Hook-dependent skills are the **least portable** feature across platforms.

## Activation Modes

| Platform | How Skills Activate |
|----------|-------------------|
| Claude Code | LLM-routed (description matching) or `/skill-name` slash command |
| OpenAI Codex | LLM-routed (description matching) or `$skill-name` mention |
| Gemini CLI | LLM-routed or `/skills` command to list and select |
| Antigravity | LLM-routed based on description matching |
| Cursor | LLM-routed, rule auto-attachment via globs, or `@rule-name` mention |

**Conversion impact**: Trigger phrases in the description work across all platforms.
The `/slash-command` syntax is Claude-specific but the underlying routing mechanism
(description-based matching) is universal.

## Subagent Comparison

| Platform | Subagent Support | Max Concurrent | Nesting |
|----------|-----------------|---------------|---------|
| Claude Code | Task tool, built-in + custom types | 10 | No |
| OpenAI Codex | None (feature request) | N/A | N/A |
| Gemini CLI | Experimental sub-agents, A2A protocol | Unknown | Unknown |
| Antigravity | Agent Manager ("Mission Control") | Parallel | Unknown |
| Cursor | Background Agents (Ultra plan only) | Single-level | No |

## Tier Conversion Notes

### Tier 1: Single Skill (SKILL.md only)
- **Converts cleanly** to all platforms
- Just copy SKILL.md with frontmatter adjustments
- Generate platform instruction file from description

### Tier 2: Skill + Scripts
- **Converts well** -- scripts are language-agnostic
- Copy SKILL.md + scripts/ directory
- Verify script paths in instructions match target structure

### Tier 3: Multi-Skill Orchestrator
- **Partial conversion** -- routing table is Claude-specific
- Each sub-skill converts independently
- Main orchestrator needs manual adaptation per platform
- Codex: routing can use `$sub-skill` mention syntax
- Gemini: routing relies on description-based activation
- Cursor: relies on description-based matching

### Tier 4: Full Ecosystem
- **Manual review required** for subagent delegation
- Agents (Task tool) are Claude Code specific
- Scripts and reference files convert cleanly
- Platform instruction files should aggregate key info
- MCP servers need config format conversion

## Platform-Specific Warnings

### Codex
- `allowed-tools` is in the spec but parser ignores it in practice
- Agent/Task delegation has no direct equivalent
- `openai.yaml` is optional but recommended for UI metadata
- AGENTS.md supports hierarchical loading (root to CWD)
- AGENTS.override.md can override instructions per directory

### Gemini CLI
- No `allowed-tools` equivalent -- all tools available by default
- Experimental sub-agents available but not production-ready
- Skills discovered via `.gemini/skills/` path scanning
- GEMINI.md is the project instruction file
- Can natively read AGENTS.md via configurable filename setting

### Antigravity
- `name` field is optional in frontmatter (defaults to dirname)
- Workspace skills in `.agent/skills/`, global in `~/.gemini/antigravity/skills/`
- Supports `{{SKILL_PATH}}` and `{{WORKSPACE_PATH}}` template variables
- Agent Manager provides multi-agent orchestration
- No `allowed-tools` or skill-scoped hooks

### Cursor
- Native SKILL.md support since v2.4 (January 2026)
- Rules (`.cursor/rules/*.mdc`) have 3-field frontmatter only
- Background Agents require Ultra/Teams/Enterprise plan
- Single-level subagents only (no nesting)
- 6 hook events (beta) with blocking support
- `globs` + `alwaysApply: true` quirk: globs are ignored
- MCP config format identical to Claude's `.mcp.json`
