# Agent Skills Standard: a cross-platform deep dive

**The four major AI coding agents — Claude Code, OpenAI Codex, Google Antigravity, and Cursor — have converged on a shared skill format centered on SKILL.md files with YAML frontmatter, published as the Agent Skills Standard at agentskills.io on December 18, 2025.** This convergence is remarkable: 18 agent platforms now consume the same skill definition format, enabling portable "agent plugins" for the first time. Yet beneath this shared surface, each platform diverges significantly in instruction files, hook systems, configuration formats, and subagent architectures. This report maps every documented field, path, and behavior across all four platforms as of February 14, 2026, citing exact sources throughout.

---

## 1. Claude Code (Anthropic)

### A. Skill and extension file format

The skill definition file is **SKILL.md**, placed inside a named directory matching the skill's `name` field. The project-level instruction file is **CLAUDE.md**, a plain Markdown file at the project root that Claude Code reads at session start and injects as a user message following its system prompt.

SKILL.md uses **YAML frontmatter** between `---` delimiters. The open standard (agentskills.io/specification) defines **6 fields**:

| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Max 64 chars; lowercase letters, numbers, hyphens; must match parent directory name |
| `description` | **Yes** | string | Max 1024 chars; describes what skill does AND when to trigger it |
| `license` | No | string | License name or reference to bundled LICENSE file |
| `compatibility` | No | string | Max 500 chars; environment requirements |
| `metadata` | No | map(string→string) | Arbitrary key-value pairs (author, version, etc.) |
| `allowed-tools` | No | string (space-delimited) | Pre-approved tools; **experimental** across all platforms |

Claude Code extends these with **proprietary fields** not in the open spec: `context` (set to `"fork"` for subagent execution), `agent` (e.g., `"Explore"`, `"Plan"`), `model` (`opus`, `sonnet`, `haiku`), `disable-model-invocation` (boolean), `user-invocable` (boolean), `hooks` (object for lifecycle hooks), and `mode` (boolean for mode commands like debug-mode). These extensions are documented at code.claude.com/docs/en/skills.

**SKILL.md body** is recommended under **500 lines / ~5,000 tokens**. At session start, only name+description metadata (~100 tokens per skill) loads; the total budget for all skill descriptions is **2% of context window** with a **16,000-character fallback**. Full instructions and resources load on demand via the spec's three-tier progressive disclosure model. No formal JSON schema exists for SKILL.md; the spec at agentskills.io is the canonical reference. A validation tool, `skills-ref validate ./my-skill`, ships in the agentskills/agentskills repo.

### B. File paths and discovery

Project-level skills live at **`.claude/skills/<skill-name>/SKILL.md`**. User/global skills live at **`~/.claude/skills/<skill-name>/SKILL.md`**. Directories added via `--add-dir` are also scanned with live change detection.

Discovery works through **progressive disclosure**: at startup, Claude pre-loads all skill metadata into the system prompt. When a user request semantically matches a skill's description, Claude reads the full SKILL.md. When the skill references additional files in `scripts/`, `references/`, or `assets/`, those load on demand. Skills are **model-invoked** by default — Claude autonomously decides when to activate them — unless `disable-model-invocation: true` restricts activation to explicit `/skill-name` slash commands.

Priority when skills share names: **enterprise > personal > project**. For settings generally: managed settings > policies > personal global. File references should stay **one level deep** from SKILL.md; deeply nested chains are discouraged.

### C. Configuration files

MCP servers are configured in **`.mcp.json`** (project root, version-controlled) and **`~/.claude.json`** (user-scoped). Format is JSON with an `mcpServers` key. Each server entry specifies `command`, `args`, and `env` for stdio transport, or `type: "http"`, `url`, and `headers` for HTTP transport. Three scopes exist: **local** (default, personal per-project), **project** (shared via `.mcp.json`), and **user** (all projects via `~/.claude.json`). Enterprise teams use `managed-mcp.json` for admin-controlled servers.

The main settings files are **`~/.claude/settings.json`** (personal global), **`.claude/settings.json`** (project shared), and **`.claude/settings.local.json`** (personal project overrides, not committed to git). All use **JSON** format. A notable known issue: `~/.claude/settings.json` does NOT work for MCP servers despite some documentation suggesting otherwise (GitHub issue #4976 on anthropics/claude-code).

### D. Instruction file handling

CLAUDE.md files follow a hierarchical discovery pattern. Files in **parent directories** above the working directory load in full at launch. The working directory's CLAUDE.md loads next. **Child directory** CLAUDE.md files load on demand when Claude reads files in those directories. Additional locations include `.claude/CLAUDE.md` and `.claude/rules/*.md` (all automatically loaded as project memory). **CLAUDE.local.md** is auto-added to `.gitignore` for private preferences.

CLAUDE.md supports an **import syntax**: `@path/to/file` pulls referenced files into context. Rules in `.claude/rules/` can be scoped to specific file patterns using YAML frontmatter with a `paths` field (e.g., `paths: ["src/api/**/*.ts"]`). More specific instructions always take precedence over broader ones.

### E. Agent and subagent system

Claude Code has the most mature subagent system among the four platforms. The **Task tool** spawns up to **10 concurrent subagents**, each with its own context window and execution loop. Built-in agent types include **general-purpose** (full tool access), **Explore** (fast, read-only codebase search), **Plan** (architecture planning), and **claude-code-guide** (documentation lookup).

Custom agent types are stored as Markdown files with YAML frontmatter in **`~/.claude/agents/`** (user) or **`.claude/agents/`** (project). Agent definitions can specify name, description, model, allowed tools, and associated skills. Skills can trigger subagent execution via `context: fork` and `agent: <type>` in frontmatter. One limitation: **sub-agents cannot spawn nested sub-agents** — the Task tool is not exposed to sub-agents (GitHub issue #4182 on anthropics/claude-code).

### F. Hook and lifecycle system

Claude Code offers the most comprehensive hook system with **13 hookable events**: Setup, SessionStart, SessionEnd, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, Notification, Stop, SubagentStart, SubagentStop, and PreCompact. Hooks run shell commands with **full user permissions — no sandbox**. Claude Code 2.1 (January 2026) added async hooks, Setup hooks, and skill-scoped hooks.

Hooks are configured in settings JSON files under a `hooks` key, with each event containing matcher patterns (regex or `"*"`) and hook arrays specifying `type` (`"command"`, `"prompt"`, or `"agent"`), `command`, optional `timeout`, and optional `async: true`. **Exit code 0** continues normally; **exit code 2** blocks the action (for PreToolUse and PermissionRequest); other non-zero codes produce non-blocking errors. Hooks can output structured JSON with `permissionDecision`, `updatedInput`, and `additionalContext` fields.

### G–H. Script execution and publishing

Skills can bundle executable scripts in `scripts/` subdirectories. Paths resolve relative to the skill root directory. The `$ARGUMENTS` placeholder enables parameterized skills — `/migrate-component SearchBar React Vue` maps to `$0=SearchBar`, `$1=React`, `$2=Vue`. Shell command output can be interpolated using `` !`command` `` syntax.

Distribution works through four channels: committing `.claude/skills/` to version control (team sharing), publishing **plugins** to the official directory at github.com/anthropics/claude-plugins-official, placing skills in `~/.claude/skills/` for personal use, or enterprise-managed deployment. The plugin system bundles skills, MCP servers, hooks, agents, and commands into a structured package installable via `/plugin install`. Community directories include **skills.sh** (Vercel, 57,160+ skills, 110,000+ installs in its first 4 days) and **skillsmp.com**.

---

## 2. OpenAI Codex

### A. Skill and extension file format

Codex uses **SKILL.md** for skills (adopting the Agent Skills Standard as of December 20, 2025) and **AGENTS.md** for project-level instructions — the equivalent of CLAUDE.md. AGENTS.md is **plain Markdown with no frontmatter required**.

SKILL.md frontmatter is intentionally minimal. Per the skill-creator spec at github.com/openai/skills, Codex parses **only `name` and `description`** — the two required fields from the open standard. The skill-creator explicitly instructs: "Do not include any other fields in YAML frontmatter." Codex ignores extra keys, meaning Claude Code's proprietary extensions like `context` or `disable-model-invocation` are silently dropped.

An optional **`agents/openai.yaml`** file sits alongside SKILL.md to provide Codex-specific UI metadata and tool dependencies:

```yaml
interface:
  display_name: "User-facing name"
  icon_small: "./assets/logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt"
dependencies:
  tools:
    - type: "mcp"
      value: "serverName"
      transport: "streamable_http"
      url: "https://example.com/mcp"
```

This file auto-triggers MCP server connections and OAuth when the skill activates. The `project_doc_max_bytes` setting defaults to **32,768 bytes (32 KiB)** for total AGENTS.md instructions.

### B. File paths and discovery

AGENTS.md discovery follows a specific precedence chain. At the **global scope**, Codex checks `$CODEX_HOME/` (defaulting to `~/.codex/`), reading `AGENTS.override.md` if it exists, otherwise `AGENTS.md`. At **project scope**, it walks from the Git root **down** to the current working directory, picking at most one file per directory. Each directory checks `AGENTS.override.md` → `AGENTS.md` → fallback filenames from `project_doc_fallback_filenames` config. All found files are **concatenated root-down**, joined with blank lines, with files closer to CWD appearing later (effectively overriding earlier guidance). Loading stops once combined size hits `project_doc_max_bytes`.

Skills are discovered from: **`.agents/skills/`** in every directory from CWD up to repo root, **`~/.agents/skills/`** (or `$AGENTS_HOME/skills/`), **`~/.codex/skills/`** (deprecated path), built-in system skills (like `$skill-creator`, `$skill-installer`, `$create-plan`), and admin-level locations (`/etc/codex/`). The `[features] skills = true` flag (on by default) enables skill support.

### C. Configuration files

Codex uses **TOML** for configuration — the only platform among the four to do so. The main config file is **`config.toml`** at `~/.codex/config.toml` (user), `.codex/config.toml` (project, trusted projects only), or `/etc/codex/config.toml` (system). A `requirements.toml` file at admin level enforces security constraints users cannot override.

MCP servers are configured **within config.toml** under `[mcp_servers.<id>]` sections, not in a separate file:

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
enabled_tools = ["tool1"]
startup_timeout_sec = 10
tool_timeout_sec = 60
```

HTTP transport uses `url` and optional `bearer_token_env_var`. CLI management: `codex mcp add`, `codex mcp list`, `codex mcp remove`, `codex mcp login/logout`. A JSON schema for config.toml exists at `codex-rs/core/config.schema.json` in the repo.

### D. Instruction file handling

AGENTS.md is free-form Markdown with no required frontmatter and no platform-specific section syntax. The `/init` slash command auto-scaffolds an AGENTS.md for the current directory. When the `[features].child_agents_md` flag is enabled, Codex appends scope and precedence guidance even when no AGENTS.md exists. Fallback filenames are configurable:

```toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
```

### E. Agent and subagent system

Codex does **not have a native built-in subagent system** comparable to Claude Code's Task tool. However, it supports two forms of multi-agent collaboration. First, **Codex can run as an MCP server** via `codex mcp-server`, exposing `codex` (start session) and `codex-reply` (continue via `threadId`) tools — enabling orchestration through the OpenAI Agents SDK with handoffs, guardrails, and traces. Second, **collaboration modes** include an explorer role, `/plan` command for plan mode, and `/review` for launching a separate review agent. Max-depth guardrails limit recursion.

A comprehensive hook-and-subagent system (PR #11067 on github.com/openai/codex) proposes `PreToolUse`, `PostToolUse`, `AfterAgent`, `SessionStart`, `Stop`, and `Notification` events with `HookOutcome` (Proceed/Block/Modify) — but this **has not been officially merged** as of February 2026. Native subagent support remains a feature request (issues #2604, #9846).

### F. Hook and lifecycle system

Codex's official hook support is limited to a **single notification mechanism**:

```toml
notify = ["python3", "/path/to/notify.py"]
```

This fires on `agent-turn-complete` events, passing a JSON payload with `type`, `last-assistant-message`, `input-messages`, and `thread-id`. TUI notifications filter by `["agent-turn-complete", "approval-requested"]`. The broader lifecycle hook system seen in Claude Code is **not yet available** in Codex — PR #11067 proposing it remains unmerged.

### G–H. Script execution and publishing

Skills bundle scripts in `scripts/` subdirectories, referenced by relative path from SKILL.md. Codex enforces the strongest **sandboxing** of any platform: `sandbox_mode` defaults to `read-only`, with `workspace-write` and `danger-full-access` as alternatives. Linux uses **Landlock + seccomp** (with optional Bubblewrap), macOS uses **Seatbelt** (`sandbox-exec`), and Windows has an experimental restricted-token sandbox. Execution policy rules (`codex execpolicy`) provide fine-grained command control.

Skills are installed via the built-in **`$skill-installer`** skill ("install the linear skill from the .experimental folder") or manually placed in `~/.codex/skills/` or `.agents/skills/`. The **`$skill-creator`** skill scaffolds new skills interactively. OpenAI maintains a curated catalog at github.com/openai/skills. There is no official first-party marketplace; distribution relies on Git repos, `$skill-installer`, and community registries like skills.sh.

---

## 3. Google Antigravity

### A. Skill and extension file format

**Google Antigravity is Google's agent-first IDE**, built by Google DeepMind on top of VS Code, released in public preview on **November 18, 2025**, and powered by Gemini 3 Pro. **There is no public GitHub repository for Antigravity itself** — it is proprietary, distributed via antigravity.google/download. However, the terminal-based sibling **Gemini CLI** is open source at github.com/google-gemini/gemini-cli (90,000+ stars), and both share the same skill/extension system.

Both tools use **SKILL.md** following the Agent Skills Standard. The project-level instruction file is **GEMINI.md** — the equivalent of CLAUDE.md. SKILL.md uses the same 6-field YAML frontmatter as the open standard. One implementation difference: in Antigravity, `name` is **not strictly mandatory** — if omitted, it defaults to the directory name. In Gemini CLI, both `name` and `description` are required per the standard.

Template variables **`{{SKILL_PATH}}`** and **`{{WORKSPACE_PATH}}`** provide portable path references within skill instructions — a feature unique to the Google implementation.

### B. File paths and discovery

Path conventions differ between Antigravity (IDE) and Gemini CLI:

**Antigravity** stores workspace skills at **`<workspace-root>/.agent/skills/`** and global skills at **`~/.gemini/antigravity/skills/`**. Rules live at **`.agent/rules/`** (project) with modes `always_on` (default) or `manual` (activated via `@rule-name`). Workflows live at **`.agent/workflows/`** (project) and **`~/.gemini/antigravity/global_workflows/`** (global).

**Gemini CLI** stores workspace skills at **`.gemini/skills/`** and user skills at **`~/.gemini/skills/`**. Extensions (a broader concept bundling skills, MCP servers, and tools) live at **`.gemini/extensions/`** (project) or **`~/.gemini/extensions/`** (global).

Discovery uses the same **progressive disclosure** pattern: metadata loads at session start, full SKILL.md loads on semantic match with the user's request, and resources load on demand. A consent prompt appears before skill activation. **Priority order: workspace > user > extension.** Both tools share `~/.gemini/GEMINI.md` for global rules, which is a documented configuration conflict (GitHub issue #16058 on google-gemini/gemini-cli).

### C. Configuration files

GEMINI.md uses plain Markdown with no required frontmatter. It supports **modular imports** via `@./path/to/file.md` syntax. The filename is configurable in `settings.json`:

```json
{ "context": { "fileName": ["AGENTS.md", "CONTEXT.md", "GEMINI.md"] } }
```

This makes Gemini CLI uniquely flexible — it can natively read AGENTS.md files from Codex projects.

MCP configuration lives at **`~/.gemini/antigravity/mcp_config.json`** (Antigravity) or within **`.gemini/settings.json`** / **`~/.gemini/settings.json`** (Gemini CLI). Both use JSON format with an `mcpServers` key. Antigravity recommends **≤50 tools** across all MCP servers, with ~25 for stability. Gemini CLI supports `command`, `url`, `httpUrl` transports with precedence: httpUrl > url > command.

### D. Instruction file handling

GEMINI.md follows a hierarchical discovery: global (`~/.gemini/GEMINI.md`) → project root + ancestor directories → subdirectories (respecting `.gitignore` and `.geminiignore`). All found files are **concatenated** with separators indicating origin path. Antigravity adds a layered instruction priority from security research by Mindgard: core platform safety policies (Google, immutable) → hardcoded system prompts → global user rules/workflows → local project rules/workflows → tool specifications → user chat messages. The system prompt injects rules with: *"The following are user-defined rules that you MUST ALWAYS FOLLOW WITHOUT ANY EXCEPTION."*

### E. Agent and subagent system

Antigravity features an **Agent Manager** ("Mission Control") for spawning and orchestrating multiple agents asynchronously across workspaces. A specialized **Browser Subagent** handles web interactions using a different model, with DOM capture, screenshots, and click/scroll capabilities. Multiple agents work in parallel, ideally one per workspace.

Gemini CLI supports **sub-agents** (documented as experimental at geminicli.com/docs/core/subagents/) and **remote subagents** via Agent-to-Agent (A2A) protocol (experimental `packages/a2a-server` in the gemini-cli repo).

### F–H. Hooks, scripts, and publishing

Gemini CLI supports **hooks** with commands `/hooks list`, `/hooks enable <name>`, `/hooks disable <name>`. Antigravity provides terminal command auto-execution policies (Off/Auto/Turbo), allow/deny lists for commands, and a browser URL allowlist at `~/.gemini/antigravity/browserAllowlist.txt`.

Skills bundle scripts in `scripts/` with standard relative path resolution. **Checkpointing** — project snapshots before file modifications — is a Gemini CLI-unique safety feature.

Distribution channels include `gemini skills install <url>` (CLI), symlinking (`gemini skills link /path`), zip install, subdirectory install from repos, and community registries. Gemini CLI has a distinct **extensions** system: directories with `gemini-extension.json` that bundle MCP servers, tools, context files, and skills, installed via `gemini extensions install <url>`.

---

## 4. Cursor (Anysphere)

### A. Skill and extension file format

Cursor's rules system has evolved through **three generations**. The legacy **`.cursorrules`** file (single plaintext file at project root, deprecated since v0.45 in January 2025) gave way to **`.cursor/rules/*.mdc`** files (MDC = Markdown with metadata, introduced v0.45). As of **Cursor v2.2 (~late 2025)**, new rules are created as **folders** in `.cursor/rules/`, each containing a `RULE.md` file. As of **Cursor v2.4 (January 22, 2026)**, Cursor natively supports **SKILL.md** files via the Agent Skills Standard, stored in `.cursor/skills/` (project) or `~/.cursor/skills/` (global).

MDC/RULE files use YAML frontmatter with **only 3 native fields** — the smallest schema of any platform:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Optional (required for agent-requested rules) | Purpose description; agent uses this to decide relevance |
| `globs` | string (comma-separated) | Optional (required for auto-attached rules) | File patterns, e.g., `*.ts,src/**/*.tsx` |
| `alwaysApply` | boolean | Optional (default: false) | Always include in context regardless of file matching |

No formal schema or spec is published. No documented max file size exists; community best practice targets **~25–50 lines per rule**.

### B. File paths and discovery

Project rules live at **`.cursor/rules/*.mdc`** (or RULE.md folders in v2.2+). User rules are set in **Cursor Settings → Rules** (plain text, no MDC support). Team rules (Enterprise feature) are plain text applied organization-wide. Skills (v2.4+) live at **`.cursor/skills/<name>/SKILL.md`** (project) or **`~/.cursor/skills/<name>/SKILL.md`** (global).

Frontmatter values determine **4 rule types**: **Always** (`alwaysApply: true`) — always in context; **Auto Attached** (`globs` set, `alwaysApply: false`) — attached when matching files are referenced; **Agent Requested** (`description` set, no globs) — AI decides relevance; **Manual** (no frontmatter set) — only activated with `@ruleName`. A critical behavioral quirk: if both `alwaysApply: true` and `globs` are set, **globs are ignored**. Auto-attached rules only trigger when a file matching the glob is referenced in chat, not merely when the agent edits a matching file.

Precedence: **Team > Project > User > Legacy `.cursorrules`**. Within project rules: Manual > Auto Attached > Agent Requested > Always.

### C. Configuration files

MCP servers use **`.cursor/mcp.json`** (project) or **`~/.cursor/mcp.json`** (global) in JSON format, supporting stdio (`command` + `args`) and Streamable HTTP/SSE (`url`) transports. Hooks use **`.cursor/hooks.json`** (project), **`~/.cursor/hooks.json`** (global), or **`/etc/cursor/hooks.json`** (enterprise), all merged. General settings are VS Code-based (`settings.json` internally).

### D. Instruction file handling and cross-platform compatibility

Cursor can consume **SKILL.md** natively as of v2.4. **AGENTS.md** support is in progress — references in the cursor-rules-reference docs state "We recommend migrating to Project Rules or to AGENTS.md," and a Sentry issue notes full support for nested AGENTS.md planned for a future version. **CLAUDE.md** is not natively consumed but can be referenced manually via `@CLAUDE.md`. A community tool (`cursor-rules-to-claude` on GitHub) converts Cursor rules to CLAUDE.md format.

Rules are the **first context loaded** — injected before the AI processes the user's prompt. All applicable rules merge; higher-precedence sources win conflicts. Rules only affect **Agent mode** (Chat/Composer) — they do NOT impact Cursor Tab completions or Inline Edit (Cmd+K).

### E. Agent and subagent system

Cursor introduced **Subagents** in **v2.4 (January 22, 2026)** — independent agents that run in parallel with their own context, configurable prompts, tool access, and models. Default subagents handle codebase research, terminal commands, and parallel work streams. Cursor's subagents are reportedly **single-level** (no nesting), unlike Claude Code's which can be multi-level.

Cursor offers multiple agent modes: **Agent Mode** (⌘. toggle, autonomous editing and commands), **Plan Mode** (asks clarifying questions first), **Ask Mode** (answers without changes), **YOLO/Auto-run Mode** (no permission prompts), and **Background Agents** (isolated Ubuntu VMs, works on branches, opens PRs — available for Ultra/Teams/Enterprise). **Composer 1.5**, Cursor's own agentic coding model with self-summarization and 20x scaled RL, launched February 9, 2026.

### F. Hook and lifecycle system

Cursor's hook system (beta since v1.7, ~October 2025) provides **6 lifecycle events**: `beforeSubmitPrompt`, `beforeShellExecution`, `beforeMCPExecution`, `beforeReadFile`, `afterFileEdit`, and `stop`. Three events support **blocking** (allow/deny/ask): `beforeShellExecution`, `beforeMCPExecution`, and `beforeReadFile`. Hooks output structured JSON with `continue`, `permission`, `userMessage`, and `agentMessage` fields. January 2026 updates made hooks **10–20x faster**. The definitive reference is Scott Chacon's (GitHub co-founder) deep dive at blog.gitbutler.com/cursor-hooks-deep-dive.

### G–H. Script execution and publishing

Rules do not execute scripts directly — they are context/instructions. **Hooks** execute arbitrary shell commands. Skills (v2.4+) can include `scripts/` directories the agent can run. No built-in sandboxing for hooks; Background Agents run in isolated VMs.

Distribution is through version control (`.cursor/rules/` committed to repos), community repositories (awesome-cursorrules, cursor.directory, dotcursorrules.com), the `cursor-rules-CLI` npm tool for auto-downloading rules, and Cursor's Team Rules enterprise feature. For skills: `npx skills add <owner/repo>` via the skills.sh registry.

---

## Cross-platform compatibility summary

### Frontmatter field matrix

| Field | Claude Code | OpenAI Codex | Antigravity/Gemini | Cursor (Skills) | Cursor (Rules) | Standard |
|-------|------------|-------------|-------------------|-----------------|----------------|----------|
| `name` | ✅ Required | ✅ Required | ✅ Required* | ✅ Required | ❌ N/A | ✅ Required |
| `description` | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ✅ Optional | ✅ Required |
| `license` | ✅ Optional | ❌ Ignored | ✅ Optional | ✅ Optional | ❌ N/A | ✅ Optional |
| `compatibility` | ✅ Optional | ❌ Ignored | ✅ Optional | ✅ Optional | ❌ N/A | ✅ Optional |
| `metadata` | ✅ Optional | ❌ Ignored | ✅ Optional | ✅ Optional | ❌ N/A | ✅ Optional |
| `allowed-tools` | ✅ Experimental | ❌ Ignored | ✅ Experimental | Unknown | ❌ N/A | ✅ Experimental |
| `context` | ✅ (e.g., "fork") | ❌ | ❌ | ❌ | ❌ | ❌ Proprietary |
| `agent` | ✅ (e.g., "Explore") | ❌ | ❌ | ❌ | ❌ | ❌ Proprietary |
| `model` | ✅ (opus/sonnet/haiku) | ❌ | ❌ | ❌ | ❌ | ❌ Proprietary |
| `disable-model-invocation` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ Proprietary |
| `globs` | ❌ | ❌ | ❌ | ❌ | ✅ Optional | ❌ Cursor-only |
| `alwaysApply` | ❌ | ❌ | ❌ | ❌ | ✅ Optional | ❌ Cursor-only |

*Antigravity defaults to directory name if `name` omitted; Gemini CLI requires it.

### Instruction file comparison

| Feature | Claude Code | OpenAI Codex | Antigravity/Gemini | Cursor |
|---------|------------|-------------|-------------------|--------|
| **Instruction file** | CLAUDE.md | AGENTS.md | GEMINI.md | .cursor/rules/*.mdc |
| **Override file** | CLAUDE.local.md | AGENTS.override.md | ❌ | ❌ |
| **Frontmatter** | Optional (paths field) | None | None | YAML (3 fields) |
| **Import syntax** | `@path/to/file` | ❌ | `@./path/to/file.md` | `@filename` (context ref) |
| **Config format** | JSON | TOML | JSON | JSON (VS Code) |
| **MCP config file** | .mcp.json | config.toml | mcp_config.json / settings.json | .cursor/mcp.json |
| **Can read other formats** | ❌ | ❌ | ✅ AGENTS.md (configurable) | ✅ SKILL.md (v2.4+) |

### Hook system comparison

| Feature | Claude Code | OpenAI Codex | Antigravity/Gemini | Cursor |
|---------|------------|-------------|-------------------|--------|
| **Hook events** | 13 | 1 (notify only) | Partial (CLI hooks) | 6 |
| **Can block actions** | ✅ (exit code 2) | ❌ | ❌ | ✅ (allow/deny/ask) |
| **Async hooks** | ✅ (Jan 2026) | ❌ | ❌ | ❌ |
| **Skill-scoped hooks** | ✅ (Jan 2026) | ❌ | ❌ | ❌ |
| **Config location** | settings.json | config.toml (notify only) | settings.json | hooks.json |
| **Sandboxing** | None (full permissions) | N/A | Policy-based | None (full permissions) |

### Subagent comparison

| Feature | Claude Code | OpenAI Codex | Antigravity | Cursor |
|---------|------------|-------------|-------------|--------|
| **Native subagents** | ✅ (Task tool) | ❌ (feature request) | ✅ (Agent Manager) | ✅ (v2.4, Jan 2026) |
| **Max concurrent** | 10 | N/A | Multiple (1 per workspace) | Unknown |
| **Nesting** | Single-level only | N/A | Unknown | Single-level only |
| **Custom agent types** | ✅ (.claude/agents/) | ❌ | ✅ (workflows) | Partial (community) |
| **Background agents** | ❌ | ❌ | ❌ | ✅ (isolated VMs) |
| **As MCP server** | ❌ | ✅ (codex mcp-server) | ❌ | ❌ |

### Sandbox comparison

| Feature | Claude Code | OpenAI Codex | Antigravity/Gemini | Cursor |
|---------|------------|-------------|-------------------|--------|
| **Sandbox model** | Permission-based | OS-level (Landlock/Seatbelt) | Policy-based (Off/Auto/Turbo) | Approval-based |
| **Default** | Ask permission | Read-only | Auto | Ask permission |
| **Network isolation** | Configurable | Configurable | Configurable | No |
| **VM isolation** | ❌ | ❌ | ❌ | ✅ (Background Agents) |

---

## What each platform uniquely offers

**Claude Code exclusives** that no other platform matches: 13 lifecycle hook events (vs. 6 or fewer elsewhere), skill-scoped hooks, async hooks, `context: fork` for subagent execution within skills, `$ARGUMENTS` positional parameter system, `disable-model-invocation` to prevent autonomous skill activation, custom agent type definitions (`.claude/agents/`), output styles (separate from skills), and the most mature plugin packaging system (`.claude-plugin/plugin.json`).

**OpenAI Codex exclusives**: TOML configuration (all others use JSON), `AGENTS.override.md` per-directory override files, the strongest OS-level sandboxing (Landlock + seccomp on Linux, Seatbelt on macOS), Codex-as-MCP-server pattern for orchestration, `agents/openai.yaml` for UI metadata and dependency declaration, execution policy rules, and `requirements.toml` for admin security enforcement.

**Google Antigravity exclusives**: Agent Manager ("Mission Control") for multi-workspace agent orchestration, dedicated Browser Subagent for web interactions, `{{SKILL_PATH}}` / `{{WORKSPACE_PATH}}` template variables, configurable instruction filename (can natively read AGENTS.md or GEMINI.md), Gemini CLI extensions system (`gemini-extension.json`), project checkpointing before modifications, A2A (Agent-to-Agent) protocol support, and workflows (`.agent/workflows/`).

**Cursor exclusives**: Four-type rule classification system (Always/Auto Attached/Agent Requested/Manual), glob-based file pattern matching for rule activation, Background Agents in isolated Ubuntu VMs, Composer 1.5 (Cursor's own agentic coding model), `beforeReadFile` hook for content filtering before LLM sees it, deep links for one-click MCP installation (`cursor://...`), and the most seamless multi-format consumption (reads both SKILL.md and its own .mdc rules natively).

---

## Changes in the last 3 months (December 2025 – February 2026)

The **Agent Skills Standard** launched December 18, 2025, and was adopted by Codex the next day (December 20). This single event transformed the ecosystem from fragmented, platform-specific formats to a shared portable standard adopted by **18 platforms** within two months. **skills.sh** (Vercel) launched January 20, 2026, recording 110,000+ skill installs across 17 agents in its first 4 days.

**Claude Code 2.1** (January 2026) added async hooks, Setup hooks, skill-scoped hooks, PermissionRequest hooks, the `agent` and `prompt` hook types, and Skills as a distinct context category. The Claude Agent SDK (renamed from Claude Code SDK) launched with TypeScript and Python support.

**Cursor v2.4** (January 22, 2026) was the platform's biggest update in this period: native Subagents, SKILL.md support via Agent Skills Standard, image generation, and Cursor Blame (Enterprise). **Composer 1.5** followed on February 9, 2026. Rules format shifted from `.mdc` files to RULE.md folders in v2.2.

**Google Antigravity** entered public preview November 18, 2025. The Google Developers Blog published a detailed "Build with Google Antigravity" guide on February 11, 2026.

**OpenAI Codex** steadily added skill management features, with the `$skill-installer` and `$skill-creator` built-in skills, `.agents/skills/` as the standard project-level path (replacing the deprecated `~/.codex/skills/`), and multi-agent collaboration improvements with explorer roles and max-depth guardrails.

## Conclusion

The Agent Skills Standard represents a genuine interoperability breakthrough — a single SKILL.md with two required YAML fields (`name`, `description`) works across 18 agent platforms today. But the standard is deliberately "under-specified" (Simon Willison's words), covering only the portable core. Real differentiation happens in the layers above: Claude Code leads in lifecycle hooks (**13 events**, async, skill-scoped) and subagent architecture (custom agent types, context forking). Codex leads in sandboxing (OS-kernel-level isolation) and configuration rigor (TOML with JSON schema validation). Antigravity leads in multi-workspace orchestration and browser automation. Cursor leads in rule granularity (glob-based activation, four rule types) and now matches the field with SKILL.md support and subagents as of January 2026.

The most consequential gap is **hooks**. Claude Code's 13-event system dwarfs Codex's single notification hook and Cursor's 6-event beta. Any skill that relies on `PreToolUse` blocking or `SubagentStart`/`SubagentStop` lifecycle management is Claude Code-only. The `allowed-tools` field — the spec's only tool-permission mechanism — remains experimental and inconsistently implemented, meaning **portable skills cannot yet reliably request tool access**. Teams building cross-platform skills should stick to the 6 standard frontmatter fields, keep instructions in pure Markdown, bundle scripts in `scripts/`, and test on at least two platforms before publishing.