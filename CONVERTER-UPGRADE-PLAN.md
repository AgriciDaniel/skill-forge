# Skill Forge Converter — Upgrade Plan

> Created: 2026-02-14
> Purpose: Carry into a fresh Claude Code conversation to continue work
> Research source: `agent-skills-standard.md` (deep research, Feb 14 2026)

---

## What Already Exists

We built `/skill-forge convert` as sub-skill #6 in the Skill Forge ecosystem. Current files:

| File | Purpose |
|------|---------|
| `skill-forge/scripts/convert_skill.py` (~480 lines) | Main conversion engine |
| `skill-forge/references/platforms.md` (~180 lines) | Platform reference (needs major update) |
| `skills/skill-forge-convert/SKILL.md` (~130 lines) | Sub-skill instructions |
| `agents/skill-forge-converter.md` (~50 lines) | Conversion agent |
| `skill-forge/SKILL.md` | Updated with convert routing |
| `install.sh` | Updated with convert help |

**Current targets**: Codex, Gemini (combined), Antigravity

**What it does today**:
- Parses SKILL.md frontmatter, classifies fields (portable/adaptable/claude-only)
- Strips Claude-only fields, generates platform SKILL.md
- Generates instruction files (AGENTS.md, GEMINI.md)
- Generates `agents/openai.yaml` for Codex
- Converts MCP config (JSON → TOML for Codex)
- Adapts body content (path replacements, warning patterns)
- Calculates compatibility score
- Generates multi-platform install script
- Supports `--dry-run`, `--include-mcp`, `--output` flags

---

## What the Research Revealed (Gaps & Corrections)

### 1. Cursor Is a 4th Platform (MISSING ENTIRELY)

Cursor v2.4 (Jan 22, 2026) now natively supports SKILL.md via Agent Skills Standard.

| Property | Value |
|----------|-------|
| Skill path (project) | `.cursor/skills/<name>/SKILL.md` |
| Skill path (global) | `~/.cursor/skills/<name>/SKILL.md` |
| Instruction file | `.cursor/rules/*.mdc` (or RULE.md folders in v2.2+) |
| MCP config | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) |
| Config format | JSON |
| Frontmatter | Standard 6 fields supported for SKILL.md |
| Rules frontmatter | Only 3 fields: `description`, `globs`, `alwaysApply` |
| Rule types | Always, Auto Attached, Agent Requested, Manual |

**Action**: Add `cursor` as a 4th conversion target.

### 2. Gemini CLI and Antigravity Are SEPARATE Platforms

We currently treat them as one. They have different paths:

| | Gemini CLI | Antigravity |
|---|-----------|-------------|
| Skill path (project) | `.gemini/skills/` | `.agent/skills/` |
| Skill path (global) | `~/.gemini/skills/` | `~/.gemini/antigravity/skills/` |
| Instruction file | GEMINI.md | GEMINI.md |
| MCP config | `.gemini/settings.json` | `~/.gemini/antigravity/mcp_config.json` |
| Extensions | `.gemini/extensions/` (gemini-extension.json) | `.agent/workflows/` |
| Template vars | No | `{{SKILL_PATH}}`, `{{WORKSPACE_PATH}}` |

**Action**: Split into `gemini` and `antigravity` as separate targets (5 total).

### 3. Path Corrections Needed

Current `convert_skill.py` has these path mappings that need updating:

```python
# CURRENT (some are wrong)
PLATFORM_PATHS = {
    "codex": {"project": ".agents/skills", "user": "~/.agents/skills"},
    "gemini": {"project": ".gemini/skills", "user": "~/.gemini/skills"},
    "antigravity": {"project": ".agent/skills", "user": "~/.gemini/antigravity/skills"},
}

# SHOULD BE (5 targets)
PLATFORM_PATHS = {
    "codex": {"project": ".agents/skills", "user": "~/.agents/skills"},
    "gemini": {"project": ".gemini/skills", "user": "~/.gemini/skills"},
    "antigravity": {"project": ".agent/skills", "user": "~/.gemini/antigravity/skills"},
    "cursor": {"project": ".cursor/skills", "user": "~/.cursor/skills"},
}
```

Note: Codex paths are confirmed correct. Gemini/Antigravity paths are confirmed correct. Cursor is new.

### 4. Cursor Rule Generation (NEW FEATURE)

Beyond SKILL.md conversion, we should optionally generate a `.cursor/rules/` rule equivalent:

```yaml
---
description: "Same as skill description"
alwaysApply: false
---
```

This gives Cursor users a native rule file alongside the SKILL.md. Only 3 frontmatter fields: `description`, `globs`, `alwaysApply`.

### 5. Codex AGENTS.override.md (NEW)

Codex supports `AGENTS.override.md` per-directory override files. Our converter should note this in the output report but not generate it (it's a user customization file).

### 6. Gemini Extensions System (NEW)

Gemini CLI has an extensions system with `gemini-extension.json` that bundles MCP servers, tools, context files, and skills. For complex Tier 3-4 skills, we could optionally generate this manifest.

```json
{
  "name": "skill-name",
  "description": "...",
  "skills": ["./skills/"],
  "mcpServers": { ... }
}
```

### 7. Antigravity Template Variables (NEW)

Antigravity supports `{{SKILL_PATH}}` and `{{WORKSPACE_PATH}}` template variables in skill instructions. When converting body content, we should replace hardcoded relative paths with these variables where appropriate.

### 8. Gemini Configurable Instruction Filename

Gemini CLI can be configured to read AGENTS.md natively via settings:
```json
{ "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
```
Our install script should mention this option.

### 9. MCP Config Locations Updated

| Platform | MCP Config File | Format |
|----------|----------------|--------|
| Claude | `.mcp.json` + `~/.claude.json` | JSON |
| Codex | `~/.codex/config.toml` `[mcp_servers]` | TOML |
| Gemini CLI | `.gemini/settings.json` `mcpServers` | JSON |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` | JSON |
| Cursor | `.cursor/mcp.json` | JSON |

### 10. Feature Parity Warnings (Expanded)

Claude Code features with NO equivalent elsewhere:

| Feature | Codex | Gemini | Antigravity | Cursor |
|---------|-------|--------|-------------|--------|
| 13 hook events | 1 (notify) | Partial | Partial | 6 (beta) |
| Skill-scoped hooks | No | No | No | No |
| Async hooks | No | No | No | No |
| `context: fork` | No | No | No | No |
| `$ARGUMENTS` system | No | No | No | No |
| `disable-model-invocation` | No | No | No | No |
| Custom agent types | No | No | Workflows | Partial |
| Output styles | No | No | No | No |
| Plugin system | No | No | Extensions | No |

---

## Implementation Plan

### Phase 1: Update convert_skill.py (Core Changes)

**1a. Add Cursor as 4th target**
- Add `cursor` to `PLATFORM_PATHS`, `PLATFORM_INSTRUCTION_FILES`, `BODY_REPLACEMENTS`
- Cursor instruction file: generate `.cursor/rules/<name>.mdc` with 3-field frontmatter
- Cursor MCP: `.cursor/mcp.json` (JSON, same format as Claude's `.mcp.json`)
- Add `generate_cursor_output()` function following existing pattern
- Update CLI `--target` choices to include `cursor`

**1b. Split gemini and antigravity**
- They're already separate targets in the CLI — verify path mappings are correct
- Add Antigravity template variable replacement (`{{SKILL_PATH}}`, `{{WORKSPACE_PATH}}`)
- Add Gemini extension manifest generation (`gemini-extension.json`) for Tier 3-4

**1c. Update body content adaptation**
- Add Cursor path replacements (`.claude/` → `.cursor/`, `CLAUDE.md` → `.cursor/rules/`)
- Add Antigravity template variable substitution where appropriate
- Expand warning patterns for Cursor-specific gotchas

**1d. Update compatibility scoring**
- Factor in hook usage (biggest portability gap)
- Factor in subagent usage (varies significantly by platform)
- Factor in `$ARGUMENTS` usage (Claude-only)

### Phase 2: Update platforms.md Reference

Rewrite `skill-forge/references/platforms.md` to include:
- All 5 platforms (Claude, Codex, Gemini, Antigravity, Cursor)
- Complete frontmatter field matrix (from research Table 1)
- Instruction file comparison table
- Hook system comparison
- Subagent comparison
- MCP config comparison
- Platform-exclusive features list

### Phase 3: Update Sub-skill and Agent

- Update `skills/skill-forge-convert/SKILL.md` to mention Cursor target
- Update `agents/skill-forge-converter.md` to know about Cursor
- Update `skill-forge/SKILL.md` triggers to include "cursor"

### Phase 4: Optional Enhancements

- **Cursor rule generation**: Generate `.mdc` rule files alongside SKILL.md
- **Gemini extension manifest**: Generate `gemini-extension.json` for complex skills
- **Reverse conversion**: Convert FROM other platforms TO Claude Code (future)
- **Validation per platform**: Validate output against each platform's constraints

---

## Key Files to Read When Starting

```
# The converter script (main code to modify)
skill-forge/scripts/convert_skill.py

# The research (source of truth for platform specs)
agent-skills-standard.md

# Current platform reference (needs rewrite)
skill-forge/references/platforms.md

# Sub-skill instructions (needs Cursor added)
skills/skill-forge-convert/SKILL.md

# Main orchestrator (needs trigger update)
skill-forge/SKILL.md

# Existing scripts for pattern reference
skill-forge/scripts/validate_skill.py
skill-forge/scripts/package_skill.py

# Agent definition (needs Cursor knowledge)
agents/skill-forge-converter.md

# Project instructions
CLAUDE.md
```

---

## Prompt to Start New Conversation

> Read `CONVERTER-UPGRADE-PLAN.md` in the project root. It contains the full plan for upgrading the Skill Forge converter to support 5 platforms (Claude, Codex, Gemini CLI, Antigravity, Cursor). The deep research is in `agent-skills-standard.md`. Start with Phase 1a: adding Cursor as a conversion target in `convert_skill.py`, then work through the plan sequentially.

---

## Architecture Note

The main SKILL.md line 155 says "orchestrates 5 specialized sub-skills" — it should say "6" since we added skill-forge-convert. Fix this while updating.