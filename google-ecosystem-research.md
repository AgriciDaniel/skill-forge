# Google Gemini Ecosystem Deep Dive: Gemini CLI, Antigravity, and Jules

**Research for Multi-Platform Skill Optimizer -- Extracted Configuration Specs**

> Note: This research combines the existing `agent-skills-multi-platform.md` findings with
> deeper extraction of Google-specific configuration formats, discovery mechanisms, and
> platform-specific extensions. Network access was unavailable during this session, so
> details are compiled from the existing research file and training data through May 2025.
> Items marked with [VERIFY] should be confirmed against live sources.

---

## 1. Gemini CLI -- Complete Configuration Reference

### Repository Overview

- **URL**: `github.com/google-gemini/gemini-cli`
- **License**: Apache 2.0
- **Language**: TypeScript (Node.js)
- **Package**: `@anthropic-ai/gemini-cli` [VERIFY exact npm package name]
- **Install**: `npm install -g @google/gemini-cli` or `npx @google/gemini-cli`

### Directory Structure (`.gemini/`)

The `.gemini/` directory is the project-level configuration root, equivalent to Claude Code's `.claude/`:

```
project-root/
  .gemini/
    settings.json          # MCP servers, sandbox config, tool allowlists
    GEMINI.md              # Project-level context/instructions
    skills/                # SKILL.md files (Agent Skills standard)
      skill-name/
        SKILL.md
        scripts/
        references/
        assets/
    agents/                # Custom sub-agent definitions (*.md)
      researcher.md
      coder.md
    commands/              # Custom slash commands (TOML format)
      my-command.toml
    extensions/            # Bundled MCP servers + context files
      my-extension/
        mcp-config.json
        context.md
    sandbox.Dockerfile     # Custom Docker sandbox image definition
  GEMINI.md                # Also valid at project root
  AGENTS.md                # Supported as alternative instruction file
```

Global configuration:
```
~/.gemini/
  settings.json            # Global settings
  GEMINI.md                # Global context (applies to all projects)
  skills/                  # Personal skills
```

---

## 2. GEMINI.md -- Complete Format Specification

### What It Is

GEMINI.md is Gemini CLI's equivalent of CLAUDE.md -- a hierarchical context file that
provides instructions and knowledge to the agent. Unlike CLAUDE.md, GEMINI.md files are
discovered at multiple directory levels and concatenated.

### Discovery Paths (Loading Order)

GEMINI.md files are discovered in this order and concatenated (all are loaded, not just
the nearest):

1. **Global**: `~/.gemini/GEMINI.md` (user-wide instructions)
2. **Ancestor directories**: Walking from project root down to CWD
   - `/path/to/project/GEMINI.md`
   - `/path/to/project/packages/GEMINI.md`
   - `/path/to/project/packages/frontend/GEMINI.md`
3. **`.gemini/` directory**: `.gemini/GEMINI.md` at each level
4. **AGENTS.md**: Also reads `AGENTS.md` files (configurable, can be disabled)

**Key difference from Claude Code**: CLAUDE.md uses a priority system where the most
specific file wins. GEMINI.md concatenates all discovered files, building up context
from global to local. The user sees the merged context via `/context` command.

### File Format

GEMINI.md is **plain Markdown** with no frontmatter requirement. There is no YAML header.

```markdown
# Project Instructions

## Build Commands
- `npm run build` to build
- `npm test` to run tests

## Code Style
- Use TypeScript strict mode
- Prefer functional components

## Architecture
The project uses a monorepo structure with packages/ directory.
Each package has its own tsconfig.json.
```

### Supported Features

| Feature | Syntax | Description |
|---------|--------|-------------|
| File imports | `@path/to/file.md` | Inline file content at load time |
| Memory command | `/memory` | Add persistent notes to GEMINI.md |
| Init command | `/init` | Generate starter GEMINI.md from project analysis |
| Context view | `/context` | View merged context from all GEMINI.md files |
| Markdown | Standard | Full Markdown support in body |

### `@import` Syntax

```markdown
# My Project

## API Reference
@references/api-guide.md

## Style Guide
@docs/style-guide.md
```

The `@path` syntax resolves relative to the GEMINI.md file's location. The referenced
file's content is inlined when context is built. This enables modular context files
without bloating a single GEMINI.md.

### `/memory` Command

Running `/memory add "Always use pnpm instead of npm"` appends the note to the
project-level GEMINI.md. This is similar to Claude Code's memory system but stores
directly in GEMINI.md rather than a separate memory file.

### `/init` Command

Generates an initial GEMINI.md by analyzing:
- Package.json / build files for build commands
- Directory structure for architecture notes
- README.md for project description
- .gitignore for project type detection

### Size Limits

No hard documented limit on GEMINI.md file size. Best practice is to keep individual
files focused and use `@import` for detailed references. The context window determines
the effective limit.

### Comparison with CLAUDE.md

| Aspect | GEMINI.md | CLAUDE.md |
|--------|-----------|-----------|
| Format | Plain Markdown | Plain Markdown |
| Frontmatter | None | None |
| Discovery | All ancestor dirs, concatenated | Priority-based (most specific wins) |
| Global path | `~/.gemini/GEMINI.md` | `~/.claude/CLAUDE.md` |
| Project path | `.gemini/GEMINI.md` or `./GEMINI.md` | `.claude/CLAUDE.md` or `./CLAUDE.md` |
| Import syntax | `@path/to/file` | None (manual file reads) |
| Memory | `/memory` writes to GEMINI.md | Separate memory files |
| Auto-generate | `/init` command | None built-in |
| AGENTS.md | Reads AGENTS.md too | Does not read AGENTS.md |
| Concatenation | All levels merged | Most specific overrides |

---

## 3. Gemini CLI settings.json -- Complete Format

### File Locations

- **Project**: `.gemini/settings.json`
- **Global**: `~/.gemini/settings.json`
- Project settings override global settings (field-level merge).

### Schema

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
      "env": {
        "API_KEY": "value"
      },
      "transport": "stdio",
      "timeout": 30000
    },
    "remote-server": {
      "url": "https://mcp.example.com/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer token"
      }
    },
    "http-server": {
      "url": "https://api.example.com/mcp",
      "transport": "http"
    }
  },
  "sandbox": {
    "type": "docker",
    "image": "custom-image:latest",
    "dockerfile": ".gemini/sandbox.Dockerfile",
    "volumes": ["/host/path:/container/path"],
    "allowNetwork": false
  },
  "toolAllowlist": ["read_file", "write_file", "run_command"],
  "toolBlocklist": ["dangerous_tool"],
  "theme": "dark",
  "model": "gemini-2.5-pro",
  "maxTokens": 65536,
  "temperature": 0.7,
  "safetySettings": {
    "harassment": "BLOCK_NONE",
    "dangerousContent": "BLOCK_MEDIUM_AND_ABOVE"
  }
}
```

### MCP Server Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | Yes (stdio) | Command to start MCP server |
| `args` | string[] | No | Command arguments |
| `env` | object | No | Environment variables for the server |
| `transport` | string | No | `"stdio"` (default), `"sse"`, `"http"` |
| `url` | string | Yes (sse/http) | Server URL for remote transports |
| `headers` | object | No | HTTP headers for remote transports |
| `timeout` | number | No | Connection timeout in ms |
| `enabled` | boolean | No | Enable/disable server (default true) |

### Three Transport Types

1. **stdio** (default): Local process, communicates via stdin/stdout
   ```json
   {
     "command": "node",
     "args": ["server.js"],
     "transport": "stdio"
   }
   ```

2. **SSE** (Server-Sent Events): Remote server with HTTP streaming
   ```json
   {
     "url": "https://mcp.example.com/sse",
     "transport": "sse"
   }
   ```

3. **HTTP** (Streamable HTTP): Standard HTTP request/response [VERIFY]
   ```json
   {
     "url": "https://api.example.com/mcp",
     "transport": "http"
   }
   ```

### Comparison with Claude Code MCP Config

| Aspect | Gemini CLI | Claude Code |
|--------|-----------|-------------|
| Config file | `.gemini/settings.json` | `.mcp.json` (project root) |
| Global config | `~/.gemini/settings.json` | `~/.claude/settings.json` |
| Format | JSON (nested in settings) | JSON (dedicated file) |
| Transports | stdio, SSE, HTTP | stdio, SSE |
| Tool filtering | `toolAllowlist` / `toolBlocklist` | `allowed-tools` in frontmatter |
| Auto-discovery | Tools, resources, prompts | Tools only |
| Prompts as commands | MCP prompts exposed as `/commands` | Not exposed |

### Key Gemini CLI MCP Features

- **Automatic tool/resource/prompt discovery**: When an MCP server connects, Gemini CLI
  automatically discovers all available tools, resources, and prompts
- **MCP prompts as slash commands**: MCP prompt templates are exposed as `/command-name`
  in the CLI, allowing direct invocation
- **Resource auto-loading**: MCP resources can be auto-loaded into context
- **Environment variable redaction**: Sensitive env vars can be filtered from logs

---

## 4. Gemini CLI Skills Support

### Agent Skills Standard Adoption

Gemini CLI supports the Agent Skills open standard (SKILL.md) natively:

- **Location**: `.gemini/skills/*/SKILL.md` (project) and `~/.gemini/skills/*/SKILL.md` (personal)
- **Format**: Identical YAML frontmatter (name + description required)
- **Progressive disclosure**: Same 3-level system (metadata -> instructions -> resources)

### Activation Mechanism (Key Difference)

Gemini CLI uses an **explicit `activate_skill` tool call** for skill activation, rather
than pure LLM routing (Claude Code) or glob matching (Cursor):

1. All skill metadata (name + description) is loaded into context
2. When the model determines a skill is relevant, it calls the `activate_skill` tool
3. The tool loads the full SKILL.md body into context
4. Supporting files (scripts/, references/) loaded on demand

This is a **more structured activation** than Claude Code's implicit LLM reasoning,
giving more control and traceability over when skills fire.

### Platform-Specific Frontmatter

Gemini CLI reads the standard Agent Skills frontmatter fields:

| Field | Support | Notes |
|-------|---------|-------|
| `name` | Full | Same spec: kebab-case, 1-64 chars |
| `description` | Full | Same spec: 1-1024 chars, no XML |
| `license` | Full | SPDX identifiers |
| `compatibility` | Full | 1-500 chars |
| `metadata` | Full | Arbitrary key-value pairs |
| `allowed-tools` | Partial | Mapped to Gemini tool names [VERIFY] |

Claude Code proprietary fields (`context`, `agent`, `model`, `hooks`, etc.) are
**ignored** by Gemini CLI (unknown fields silently skipped).

### Extensions Directory

```
.gemini/extensions/
  my-extension/
    mcp-config.json    # MCP server definition
    context.md         # Auto-loaded context when extension is active
    tools/             # Extension-specific tools
```

Extensions bundle MCP servers with contextual knowledge -- similar to skills but focused
on tool connectivity rather than procedural knowledge.

### Custom Commands (TOML)

```toml
# .gemini/commands/deploy.toml
[command]
name = "deploy"
description = "Deploy the application to staging"
prompt = "Deploy the application to the staging environment. Run tests first."
```

Custom commands are defined in TOML, unlike Claude Code's skill-based commands.
These are simpler (just a name, description, and prompt template) but less powerful
than full skills.

---

## 5. Gemini CLI Security and Sandbox Model

### Permission Model

| Mode | Flag | Behavior |
|------|------|----------|
| Default | (none) | Explicit confirmation for each action |
| YOLO | `--yolo` | Auto-approve all actions (no confirmations) |
| Sandbox | `--sandbox` | Run in Docker/container isolation |
| Custom | `--sandbox-profile` | Custom sandbox configuration |

### Sandbox Options

1. **No sandbox** (default): Full system access, confirmation prompts only
   - A **red warning** is displayed when running without sandbox
2. **macOS Seatbelt**: Similar to Claude Code's approach [VERIFY if supported]
3. **Docker**: Full container isolation via `sandbox.Dockerfile`
4. **Podman**: Alternative container runtime
5. **Custom profiles**: User-defined sandbox configurations

### Tool Allowlists/Blocklists

```json
{
  "toolAllowlist": ["read_file", "write_file", "list_directory"],
  "toolBlocklist": ["execute_command"]
}
```

These are **global** tool filters in settings.json. Unlike Claude Code's per-skill
`allowed-tools` frontmatter, Gemini CLI applies these at the project/global level.

---

## 6. Agent2Agent (A2A) Protocol

### Overview

Google is proposing the A2A protocol for remote sub-agent communication. An RFC is
at `github.com/google-gemini/gemini-cli/discussions/7822` [VERIFY discussion number].

### Key Concepts

- **Remote agents**: Sub-agents that run as independent services (not local processes)
- **Discovery**: Agents publish capabilities via a manifest endpoint
- **Invocation**: Standard HTTP/gRPC protocol for agent-to-agent calls
- **State management**: Agents maintain their own state, communicate via messages
- **Authentication**: OAuth2/API key based agent identity

### A2A vs MCP

| Aspect | A2A | MCP |
|--------|-----|-----|
| Purpose | Agent-to-agent communication | Agent-to-tool communication |
| Scope | Remote agent orchestration | Local/remote tool access |
| Protocol | HTTP/gRPC | stdio/SSE/HTTP |
| State | Stateful agents | Stateless tools |
| Discovery | Agent manifests | Tool schemas |
| Spec status | RFC/proposal stage | Production standard |

### Relevance to Skill Optimizer

A2A is complementary to skills and MCP. Skills define what an agent knows; MCP provides
tool access; A2A enables multi-agent orchestration. A multi-platform skill optimizer
should be aware of A2A but does not need to generate A2A-specific artifacts -- skills
operate at a lower level than agent-to-agent communication.

---

## 7. Google Antigravity -- Configuration Details

### What It Is

Antigravity is Google's **agent-first IDE**, announced November 18, 2025 alongside
Gemini 3. It is built on a modified VS Code fork, leveraging technology from the
Windsurf team that Google acquired for $2.4 billion.

### Architecture

- **Editor View**: Standard VS Code-like code editing
- **Agent Manager**: Dedicated panel for agent orchestration
- **Browser Integration**: Agents can launch Chrome via Gemini's Computer Use model
  to verify UI, generate screenshots, and create walkthroughs
- **Multi-model**: Supports Google (Gemini 3 Pro/Flash), Anthropic (Claude), and
  OpenAI models

### Configuration

Antigravity inherits the `.gemini/` configuration structure from Gemini CLI:

```
project-root/
  .gemini/
    settings.json      # Same format as Gemini CLI
    GEMINI.md          # Project instructions
    skills/            # Agent Skills (SKILL.md)
    agents/            # Custom agent definitions
    extensions/        # MCP bundles
  AGENTS.md            # Also supported
```

### Key Differences from Gemini CLI

| Feature | Gemini CLI | Antigravity |
|---------|-----------|-------------|
| Interface | Terminal | Full IDE |
| Browser access | None | Chrome via Computer Use |
| Visual context | None | Screenshot, UI rendering |
| Model support | Gemini only | Gemini + Claude + OpenAI |
| Skill activation | `activate_skill` tool | Progressive Disclosure (IDE-native) |
| Agent panel | None | Dedicated Agent Manager |
| Status | Stable release | Public preview |
| Cost | Free (API key) | Free preview (Gemini 3 Pro rate limits) |

### Unique Capabilities Not in Claude Code or Codex

1. **Browser-in-the-loop**: Agents can autonomously browse, verify UI, take screenshots
2. **Agent Manager UI**: Visual orchestration of multiple agents
3. **Multi-model flexibility**: Switch models per task within the same session
4. **Computer Use integration**: Gemini's native screen understanding
5. **Inherited Windsurf features**: Cascade-style multi-file editing, memory system

### Skills in Antigravity

Antigravity supports skills through the same Agent Skills standard, with
Progressive Disclosure matching Gemini CLI. The IDE context provides additional
capabilities:

- Skills can reference visual context (screenshots, UI state)
- Agent Manager can orchestrate multiple skills simultaneously
- Skills can trigger browser verification as a validation step

### Configuration Specific to Antigravity [VERIFY]

Antigravity may have additional IDE-specific settings:
```json
{
  "antigravity": {
    "browserAccess": true,
    "screenshotOnVerify": true,
    "agentPanelPosition": "right",
    "preferredModel": "gemini-3-pro"
  }
}
```

---

## 8. Jules -- Configuration Details

### What It Is

Jules is Google's **asynchronous, autonomous coding agent** that runs in ephemeral
Google Cloud VMs. It operates independently -- you assign it a task and it works
in the background, returning results asynchronously.

### Access Methods

| Method | Description |
|--------|-------------|
| Web UI | `jules.google` -- task submission and review |
| Jules Tools CLI | Command-line task management |
| Jules API | Programmatic task submission |
| GitHub integration | Triggered from issues/PRs |

### Instruction File Support

| File | Support | Notes |
|------|---------|-------|
| AGENTS.md | Primary | Jules was a co-creator of the AGENTS.md standard |
| GEMINI.md | Yes | Reads project-level GEMINI.md |
| SKILL.md | Limited [VERIFY] | May support skills in `.gemini/skills/` |
| `.gemini/settings.json` | Partial | MCP servers only (vetted list) |

### Jules Task Configuration

Tasks are submitted via the web UI, CLI, or API:

```json
{
  "repository": "github.com/user/repo",
  "branch": "main",
  "task": "Fix the authentication bug in src/auth.ts",
  "context": "The login endpoint returns 500 when email contains +",
  "constraints": {
    "maxFiles": 10,
    "testRequired": true,
    "reviewRequired": true
  }
}
```

### MCP in Jules

Jules supports **vetted MCP server integrations only** -- Google audits and approves
MCP servers before they can be used with Jules. This is a security measure since Jules
runs autonomously with write access to repositories.

Approved MCP servers include official Google services and select third-party integrations.
Custom/arbitrary MCP servers are not supported.

### Jules Pricing

| Plan | Tasks/Day | Concurrent | Cost |
|------|-----------|-----------|------|
| Free | 15 | 3 | $0 |
| Google AI Pro | 50 | 5 | $19.99/mo |
| Google AI Ultra | 300 | 10 | $124.99/mo |

### Powered By

Jules runs on **Gemini 3 Flash** (optimized for speed and code tasks).

### Key Differences from Gemini CLI

| Aspect | Jules | Gemini CLI |
|--------|-------|-----------|
| Execution | Async, cloud VMs | Sync, local |
| Instruction file | AGENTS.md primary | GEMINI.md primary |
| MCP | Vetted only | Any |
| Skills | Limited/TBD | Full Agent Skills support |
| User interaction | None during execution | Interactive |
| Output | PR/commit/patch | Direct file changes |
| Cost | Tiered plans | Free (own API key) |

---

## 9. Cross-Platform Skill Conversion Map

### Storage Path Mapping

| Platform | Project Skills Path | Personal Skills Path |
|----------|-------------------|---------------------|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.codex/skills/` | `~/.codex/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |
| Antigravity | `.gemini/skills/` | `~/.gemini/skills/` |
| Cursor | `.cursor/rules/` | N/A |
| Windsurf | `.windsurf/rules/` | N/A |
| Copilot | `.github/skills/` | N/A |
| Amazon Q | `.amazonq/rules/` | `~/.aws/amazonq/rules/` [VERIFY] |

### Instruction File Mapping

| Platform | Primary | Also Reads |
|----------|---------|------------|
| Claude Code | `CLAUDE.md` | -- |
| Codex | `AGENTS.md` | -- |
| Gemini CLI | `GEMINI.md` | `AGENTS.md` |
| Antigravity | `GEMINI.md` | `AGENTS.md` |
| Jules | `AGENTS.md` | `GEMINI.md` |
| Cursor | `.cursor/rules/*.mdc` | `AGENTS.md` |
| Windsurf | `.windsurf/rules/*.md` | `AGENTS.md` |
| Copilot | `.github/copilot-instructions.md` | `AGENTS.md` |

### MCP Configuration Mapping

| Platform | Config File | Format |
|----------|------------|--------|
| Claude Code | `.mcp.json` | Dedicated JSON |
| Codex | `config.toml` (`[mcp_servers]`) | TOML section |
| Gemini CLI | `.gemini/settings.json` (`mcpServers`) | JSON nested |
| Antigravity | `.gemini/settings.json` (`mcpServers`) | JSON nested |
| Cursor | VS Code settings | JSON |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | JSON |
| Copilot | Docker-based MCP | Dockerfile |
| Amazon Q | `.amazonq/mcp.json` | JSON |

### Activation Mechanism Mapping

| Platform | Mechanism | Description |
|----------|-----------|-------------|
| Claude Code | LLM reasoning | Pure description-based, model decides |
| Codex | LLM + explicit | `$skill-name` (explicit) or auto (implicit) |
| Gemini CLI | `activate_skill` tool | Structured tool call by model |
| Antigravity | Progressive Disclosure | IDE-native activation |
| Cursor | Glob + model | `alwaysApply`, glob match, or model decision |
| Windsurf | Glob + model | Always On, Glob, Model Decision, Manual |

### Frontmatter Compatibility Matrix

| Field | Standard | Claude Code | Codex | Gemini CLI |
|-------|----------|-------------|-------|-----------|
| `name` | Required | Required | Required | Required |
| `description` | Required | Required | Required | Required |
| `license` | Optional | Supported | Supported | Supported |
| `compatibility` | Optional | Supported | Supported | Supported |
| `metadata` | Optional | Supported | Supported | Supported |
| `allowed-tools` | Optional | Supported | Supported | Partial [VERIFY] |
| `context` | -- | `fork` | -- | -- |
| `agent` | -- | Agent types | -- | -- |
| `model` | -- | `sonnet`/`opus`/`haiku` | -- | -- |
| `disable-model-invocation` | -- | Supported | -- | -- |
| `user-invocable` | -- | Supported | -- | -- |
| `hooks` | -- | Supported | -- | -- |
| `argument-hint` | -- | Supported | -- | -- |
| `agents/openai.yaml` | -- | -- | UI metadata | -- |
| `globs` | -- | -- | -- | -- (Cursor-specific) |
| `alwaysApply` | -- | -- | -- | -- (Cursor-specific) |

---

## 10. Recommendations for the Multi-Platform Skill Optimizer

### Architecture: Shared Standard + Platform Extensions

Since all major platforms now support Agent Skills (SKILL.md) natively, the optimizer
should follow the "shared standard + extensions" approach:

```
skill-name/
  SKILL.md                    # Universal (Agent Skills standard)
  platforms/
    claude.yaml               # Claude Code extensions (context, agent, model, hooks)
    codex.yaml                # Codex extensions (agents/openai.yaml content)
    gemini.yaml               # Gemini CLI extensions (if any)
    cursor.yaml               # Cursor extensions (globs, alwaysApply)
    windsurf.yaml             # Windsurf extensions (activation mode)
  scripts/
  references/
  assets/
```

### Converter Operations

The optimizer needs these operations:

1. **Deploy** -- Copy SKILL.md to correct platform path:
   ```bash
   # Claude Code
   cp -r skill-name/ .claude/skills/skill-name/

   # Gemini CLI / Antigravity
   cp -r skill-name/ .gemini/skills/skill-name/

   # Codex
   cp -r skill-name/ .codex/skills/skill-name/
   ```

2. **Merge frontmatter** -- Overlay platform-specific fields:
   ```python
   base_frontmatter = parse_yaml("SKILL.md")
   platform_ext = parse_yaml("platforms/claude.yaml")
   merged = {**base_frontmatter, **platform_ext}
   write_skill_md(merged, body)
   ```

3. **Generate instruction files** -- For platforms that use instruction files:
   ```bash
   # Generate AGENTS.md from skill descriptions for Codex/Jules
   # Generate GEMINI.md skill references for Gemini CLI
   # Generate .cursor/rules/*.mdc for Cursor
   ```

4. **Validate** -- Per-platform validation:
   - Name format (kebab-case everywhere)
   - Description length (1024 chars everywhere)
   - No XML in frontmatter (everywhere)
   - Platform-specific field values (model names, tool names)

### Critical Optimization: Description Quality

Since descriptions are the universal activation mechanism across all platforms, the
optimizer should include a description quality scorer:

- **LLM routing** (Claude Code): Needs clear WHAT + WHEN + trigger phrases
- **Tool call** (Gemini CLI): Needs keyword-rich descriptions for `activate_skill`
- **Glob matching** (Cursor/Windsurf): Needs file type references where applicable
- **Explicit invocation** (Codex): Needs memorable `$skill-name` with good description

A good universal description works across all activation mechanisms:
```
"Performs comprehensive SEO audits on web pages and generates optimization
reports. Use when user asks to 'audit SEO', 'check SEO score', 'analyze
page rankings', 'optimize for search engines', or provides URLs for review.
Generates detailed reports with priority-ranked recommendations."
```

### What Cannot Be Converted

Some features are fundamentally platform-specific with no cross-platform equivalent:

| Feature | Platform | Status |
|---------|----------|--------|
| `context: fork` (subagents) | Claude Code | No equivalent elsewhere |
| Hooks (PreToolUse, etc.) | Claude Code | Unique to Claude Code |
| `agents/openai.yaml` | Codex | UI metadata, Codex-specific |
| Browser verification | Antigravity | Requires Computer Use |
| `activate_skill` tool | Gemini CLI | Automatic in other platforms |
| `.mdc` format | Cursor | Needs conversion to standard .md |
| Cascade memory | Windsurf | Proprietary memory system |

These should be documented as "platform-specific enhancements" and stripped during
cross-platform conversion.

---

## 11. Gaps Requiring Live Verification

The following items could not be verified due to network access restrictions and should
be confirmed against the live sources listed in the original request:

### From Gemini CLI GitHub (`github.com/google-gemini/gemini-cli`)
- [ ] Exact current directory structure (may have evolved)
- [ ] `settings.json` complete schema (field names may differ)
- [ ] Extensions directory structure and format
- [ ] Custom commands TOML format details
- [ ] Agent definition format (`.gemini/agents/*.md`)
- [ ] A2A RFC discussion number and current status
- [ ] Sandbox configuration options

### From GEMINI.md docs (`geminicli.com/docs/cli/gemini-md`)
- [ ] Exact `@import` syntax and behavior
- [ ] `/memory` command persistence mechanism
- [ ] Concatenation vs override behavior for nested GEMINI.md files
- [ ] Size limits if any

### From MCP docs (`geminicli.com/docs/tools/mcp-server`)
- [ ] Streamable HTTP transport details (vs standard HTTP)
- [ ] MCP prompts-as-commands syntax
- [ ] Resource auto-loading configuration
- [ ] Environment variable redaction syntax

### From Antigravity announcement
- [ ] Exact configuration format differences from Gemini CLI
- [ ] Agent Manager API/configuration
- [ ] Browser integration configuration
- [ ] Multi-model switching configuration

### From Jules docs (`jules.google/docs`)
- [ ] SKILL.md support status
- [ ] Vetted MCP server list
- [ ] Task API complete specification
- [ ] AGENTS.md reading behavior details

---

## 12. Quick Reference: Deploying a Skill to All Google Platforms

```bash
#!/bin/bash
# deploy-google.sh -- Deploy a skill to Gemini CLI, Antigravity, and Jules-ready repos

SKILL_DIR="$1"
SKILL_NAME=$(basename "$SKILL_DIR")

# Gemini CLI / Antigravity (same path)
mkdir -p .gemini/skills/"$SKILL_NAME"
cp -r "$SKILL_DIR"/* .gemini/skills/"$SKILL_NAME"/

# For Jules: Ensure AGENTS.md exists with skill reference
if [ ! -f AGENTS.md ]; then
  echo "# Project Agent Instructions" > AGENTS.md
  echo "" >> AGENTS.md
  echo "## Available Skills" >> AGENTS.md
fi

# Add skill reference to AGENTS.md if not present
if ! grep -q "$SKILL_NAME" AGENTS.md 2>/dev/null; then
  echo "- **$SKILL_NAME**: $(grep 'description:' "$SKILL_DIR/SKILL.md" | head -1 | sed 's/description: //')" >> AGENTS.md
fi

echo "Deployed $SKILL_NAME to .gemini/skills/ and AGENTS.md"
```
