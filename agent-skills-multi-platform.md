# Agent skill systems across AI coding platforms in 2025–2026

**The AI coding agent ecosystem has converged around a single portable skill format far faster than anyone predicted.** The Agent Skills open standard — built on the SKILL.md file format with YAML frontmatter — launched by Anthropic in December 2025 and has been adopted by **30+ platforms** including OpenAI Codex, Google Gemini CLI, GitHub Copilot, Cursor, and Windsurf within just two months. Combined with AGENTS.md for project instructions and MCP for tool connectivity, all three standards now reside under the **Agentic AI Foundation (AAIF)** at the Linux Foundation. This convergence means a universal skill optimizer is not only feasible but largely unnecessary for the core format — platform differences have narrowed to storage paths, activation modes, and vendor-specific extensions rather than fundamental format incompatibilities.

---

## 1. Claude Code: the origin of Agent Skills

Claude Code is the birthplace and reference implementation of the Agent Skills standard. Anthropic publicly introduced skills on **October 16, 2025**, then released the open specification at **agentskills.io** on **December 18, 2025** (Apache 2.0 code / CC-BY-4.0 docs). The GitHub repo lives at `github.com/agentskills/agentskills`, deliberately under a vendor-neutral organization.

### SKILL.md format specification

Each skill is a self-contained directory with a required `SKILL.md` file. The YAML frontmatter supports two **required** fields and several optional ones:

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1–64 chars, lowercase alphanumeric + hyphens, must match parent directory name |
| `description` | Yes | Max 1,024 chars; tells agents *what* the skill does and *when* to use it |
| `license` | No | SPDX identifier or reference to bundled file |
| `compatibility` | No | Max 500 chars; environment requirements |
| `metadata` | No | Arbitrary key-value map (author, version, tags) — experimental |
| `allowed-tools` | No | Space-delimited tool allowlist — experimental |

Claude Code extends the open spec with **proprietary frontmatter fields**: `context` (main vs. fork for subagent execution), `agent` (subagent type — Explore, Plan, or custom), `model` (override model selection), `disable-model-invocation`, `user-invocable`, `skills` (inject into subagent), `memory` (persistent knowledge directory), and `permissionMode`. The Markdown body contains free-form instructions with support for `$ARGUMENTS` placeholders, `!command` shell pre-processing, and `@path` file references.

The recommended skill directory structure is:
```
skill-name/
├── SKILL.md          # Required — instructions + metadata
├── scripts/          # Optional — executable Python/Bash
├── references/       # Optional — loaded on demand
└── assets/           # Optional — templates, resources
```

### Discovery, activation, and loading

Claude Code scans three locations in priority order: **personal** (`~/.claude/skills/`), **project** (`.claude/skills/`), and **plugin** (bundled with installed plugins). Monorepo support is automatic — editing files in `packages/frontend/` also discovers skills in `packages/frontend/.claude/skills/`. There is **no algorithmic routing**: all skill metadata is formatted into an `<available_skills>` XML block in the system prompt, and the LLM's reasoning alone decides invocation.

**Progressive disclosure** keeps context lean. At startup, only name + description load (~100 tokens per skill). Full SKILL.md content loads only on activation. Supporting files load only when referenced during execution. Skills activate through five modes: automatic model invocation (default), manual `/skill-name` slash command, `disable-model-invocation: true` (user-only), `user-invocable: false` (agent-only), or subagent injection via the `skills` field.

### Hooks, MCP integration, and subagents

**Hooks** are deterministic bash/prompt callbacks configured in `.claude/settings.json` that fire on 13+ events (PreToolUse, PostToolUse, SessionStart, SubagentStop, etc.). They complement skills — skills define *what* to do; hooks define *when* to do it automatically. Hooks can block actions (exit code 2), provide feedback, or inject context.

**MCP** and skills are explicitly complementary: skills provide procedural knowledge (low token cost); MCP provides dynamic tool/data connectivity. MCP servers are configured via `.mcp.json` at the project root. Skills can reference MCP tools in their `allowed-tools` field. As of early 2026, MCP has **10,000+ active servers** and **97 million monthly SDK downloads**.

**Subagents** (via `context: fork`) run skills in isolated conversations with separate history. The `agent` field selects built-in types (Explore, Plan) or custom agents from `.claude/agents/`. An experimental **Swarms** feature (discovered January 2026) enables multi-agent orchestration with a team lead delegating to specialist background agents — not yet officially released.

### 2026 updates

Key developments in early 2026 include **OpenAI Responses API adding skills support** (February 2026), the **Opus 4.6 model** with 1M token context (beta), **MCP Apps** allowing tools to return interactive UI components (January 2026), the **convergence of commands into skills** (custom slash commands unified with the skills system), and massive community growth with the **SkillsMP marketplace** listing 160,000+ skills and **skills.sh** serving as the primary distribution hub. Mintlify now auto-generates SKILL.md files from documentation, serving them at `/.well-known/skills/default/skill.md`.

### Security and sandboxing

Claude Code's sandbox uses OS-level primitives (**macOS Seatbelt**, **Linux bubblewrap**, **WSL2 bubblewrap**) providing filesystem isolation (read/write only in CWD), network isolation (approved domains only via unix domain socket proxy), and process isolation. Anthropic reports an **84% reduction in permission prompts** from sandboxing. The `allowed-tools` frontmatter grants pre-approved tool access; denylists in `.claude/settings.json` block specific tools or paths; hooks add a third programmatic layer of control.

**Key documentation links:**
- Specification: agentskills.io/specification
- GitHub: github.com/agentskills/agentskills
- Claude Code Skills Docs: code.claude.com/docs/en/skills
- Example Skills: github.com/anthropics/skills
- Sandboxing: anthropic.com/engineering/claude-code-sandboxing

---

## 2. OpenAI Codex: full convergence on the same standards

OpenAI's Codex — both the cloud coding agent at chatgpt.com/codex and the open-source Rust-based CLI (`github.com/openai/codex`) — has **fully adopted the Agent Skills standard**, using structurally identical SKILL.md files with the same metadata format and directory organization as Claude Code.

### Configuration architecture

Codex uses **TOML** as its primary configuration format via `config.toml` at three scopes: user (`~/.codex/config.toml`), project (`.codex/config.toml`), and admin (`/etc/codex/config.toml`). The `CODEX_HOME` environment variable (default `~/.codex`) controls local state storage. CLI flags accept TOML overrides with dot notation (e.g., `--config mcp_servers.context7.enabled=false`). Named **profiles** can be defined under `[profiles.<name>]` and activated with `codex --profile <name>`.

### AGENTS.md — the project instructions standard

Codex originated the **AGENTS.md** convention, now an open cross-platform standard at `agents.md` with adoption by **60,000+ open-source projects**. AGENTS.md files serve as a "README for agents" covering project structure, coding standards, build/test/lint commands, and security guardrails. Discovery uses a cascading hierarchy: `AGENTS.override.md` → `AGENTS.md` → fallback filenames, walking from CWD up to project root. The nearest file wins. OpenAI's own Codex repo contains **88 AGENTS.md files**.

AGENTS.md is now supported by: Codex, Copilot, Cursor, Gemini CLI, Jules, Windsurf, Roo Code, Aider, Factory, Zed, Warp, VS Code, Devin, and many more.

### Skills system

Codex skills use the exact Agent Skills specification — SKILL.md files with YAML frontmatter in directories containing optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml` (for UI metadata and invocation policy). Skills are discovered at `.codex/skills` (repo), `~/.codex/skills` (user), `/etc/codex/skills` (admin), and system-bundled locations.

**Invocation** supports explicit (`/skills` command or `$skill-name` mention) and implicit (description-based auto-matching). The optional `agents/openai.yaml` file can set `allow_implicit_invocation: false` to require explicit triggers. Built-in skills include `$skill-creator`, `$plan`, and `$skill-installer` for bootstrapping and installation. Curated skills live at `github.com/openai/skills`.

### MCP support

Codex has **comprehensive MCP support** with two transport types (STDIO and Streamable HTTP). Configuration lives in `config.toml` under `[mcp_servers.<name>]` sections. Full CLI management via `codex mcp add/list/remove/login/logout`. Enterprise `requirements.toml` can enforce MCP server allowlists. Notably, **Codex can itself run as an MCP server** via `codex mcp-server`, enabling multi-agent workflows through the OpenAI Agents SDK.

### Sandbox and environment

Cloud tasks run in **isolated containers** with internet disabled by default during the agent phase (enabled during setup). The `codex-universal` base image includes pre-installed languages. Container state caches for up to 12 hours. Local sandboxing uses macOS Seatbelt or Linux Landlock with configurable modes: `workspace-write` (default — write access to workspace and /tmp only) and `danger-full-access` (no sandboxing). Approval policies range from `untrusted` (approve everything) through `never` (full auto).

**Key documentation links:**
- Codex Skills: developers.openai.com/codex/skills
- AGENTS.md Guide: developers.openai.com/codex/guides/agents-md
- MCP: developers.openai.com/codex/mcp
- Config Reference: developers.openai.com/codex/config-reference
- GitHub: github.com/openai/codex
- Cloud Environments: developers.openai.com/codex/cloud/environments

---

## 3. Google Gemini ecosystem: CLI, Jules, Code Assist, and Antigravity

Google's coding agent ecosystem spans four products — Gemini CLI, Jules, Code Assist, and the new Antigravity IDE — all adopting the same open standards while adding Google-specific capabilities.

### Gemini CLI

The **open-source** (Apache 2.0) Gemini CLI at `github.com/google-gemini/gemini-cli` is the most configurable of Google's offerings. It uses **GEMINI.md** as its equivalent of CLAUDE.md — hierarchical context files discovered at global (`~/.gemini/GEMINI.md`), ancestor directories (up to project root), and subdirectories. The `/memory` command manages context; `/init` generates starter GEMINI.md files; `@path/to/file.md` syntax enables modular imports.

The `.gemini/` directory houses project configuration:

| File/Directory | Purpose |
|----------------|---------|
| `settings.json` | MCP servers, sandbox, tool allowlists |
| `GEMINI.md` | Project-level context |
| `skills/` | SKILL.md files (Agent Skills standard) |
| `agents/*.md` | Custom sub-agent definitions |
| `commands/` | Custom slash commands (TOML) |
| `extensions/` | Bundled MCP servers + context |
| `sandbox.Dockerfile` | Custom Docker sandbox image |

Gemini CLI has **first-class MCP support** with three transport types (stdio, SSE, HTTP), automatic tool/resource/prompt discovery, and MCP prompts exposed as slash commands. It supports the **Agent Skills standard** natively with skills in `.gemini/skills/` using progressive on-demand activation. Google is also proposing standardization on the **Agent2Agent (A2A) protocol** for remote sub-agents via an RFC at `github.com/google-gemini/gemini-cli/discussions/7822`.

### Jules

Jules is Google's **asynchronous, autonomous coding agent** running in ephemeral Google Cloud VMs. Out of beta since August 2025, now powered by Gemini 3 Flash. Jules reads **AGENTS.md** files for project instructions (it was a co-creator of the AGENTS.md standard) and supports vetted MCP server integrations audited by Google. Access via web UI (jules.google), Jules Tools CLI, and Jules API. Free tier offers **15 daily tasks** with 3 concurrent; Google AI Ultra ($124.99/mo) provides 20× limits.

### Google Antigravity

**Antigravity** is Google's agent-first IDE, announced **November 18, 2025** alongside Gemini 3. Built as a modified VS Code fork (leveraging the Windsurf team Google acquired for $2.4B), it features two interfaces: Editor View and Agent Manager. Agents have direct access to editor, terminal, and **browser** (via Gemini's Computer Use model) — they can autonomously launch Chrome to verify UI, generate screenshots and walkthroughs. Antigravity supports skills through Progressive Disclosure and is in **public preview** with free Gemini 3 Pro rate limits. It supports models from Google, Anthropic, and OpenAI.

### Gemini Code Assist

The IDE extension uses `.gemini/config.yaml` and `.gemini/styleguide.md` for GitHub code review customization. Agent mode in VS Code (powered by Gemini CLI) shares the CLI's full MCP and skills support. Enterprise users get code customization via Developer Connect indexing (up to 20,000 private repos).

### Security model

Gemini CLI uses explicit action confirmation by default with **YOLO mode** (`--yolo`) for auto-approval. Sandboxing options include macOS Seatbelt, Docker/Podman containers, and custom profiles. Enterprise controls include tool allowlists/blocklists, MCP server filtering, and environment variable redaction.

**Key documentation links:**
- Gemini CLI: github.com/google-gemini/gemini-cli
- GEMINI.md Docs: geminicli.com/docs/cli/gemini-md
- MCP Config: geminicli.com/docs/tools/mcp-server
- Jules: jules.google/docs
- Antigravity: developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform
- Code Assist: developers.google.com/gemini-code-assist/docs/customize-gemini-behavior-github

---

## 4. Other platforms and emerging standards

### Cursor

Cursor uses `.cursor/rules/` with **`.mdc` files** (Markdown Component) containing YAML frontmatter with `description`, `globs`, and `alwaysApply` fields. Five activation priorities exist: Local (manual `@ruleName`), Auto Attached (glob match), Agent Requested (model decides from description), Always Apply, and Legacy `.cursorrules`. Cursor also supports **AGENTS.md** and **Agent Skills (SKILL.md)** natively, plus MCP servers — making it one of the most standards-compliant platforms. The legacy `.cursorrules` plain-text file is deprecated but still functional.

### Windsurf

Windsurf (formerly Codeium) uses `.windsurf/rules/` with `.md` files containing YAML frontmatter, supporting four activation modes: Always On, Glob-based, Model Decision, and Manual. MCP configuration lives at `~/.codeium/windsurf/mcp_config.json`. Windsurf has adopted all three open standards: **AGENTS.md** (full cascading support), **Agent Skills** (SKILL.md), and **MCP**. Its "Memories" system provides persistent learning across sessions.

### Amazon Q Developer

Amazon Q uses `.amazonq/rules/` with plain Markdown files automatically loaded from the rules directory. Uniquely, Q supports **custom agents** in its CLI defined via JSON with explicit capabilities (`fs_read`, `fs_write`), per-agent MCP server scoping, and dynamic context hooks. MCP configuration lives at `.amazonq/mcp.json` (workspace) and `~/.aws/amazonq/mcp.json` (global). Enterprise customizations use S3-hosted codebases for organization-wide suggestions.

### GitHub Copilot

Copilot uses `.github/copilot-instructions.md` for repository-wide instructions, `.github/instructions/*.instructions.md` with `applyTo` frontmatter for path-specific rules, and `.github/agents/*.agent.md` for agent definitions. Full **AGENTS.md** and **Agent Skills** support via VS Code. MCP server integration via Docker-based servers. Organization-level instructions configurable through GitHub settings.

### The Agentic AI Foundation (AAIF)

Formed **December 9, 2025** under the Linux Foundation, AAIF provides neutral governance for all three core standards. Co-founded by Anthropic, Block (goose), and OpenAI with supporting members AWS, Google, Microsoft, Cloudflare, and Bloomberg. Founding projects: **MCP**, **AGENTS.md**, and **goose** (open-source agent framework).

---

## 5. Cross-platform comparison matrix

| Dimension | Claude Code | OpenAI Codex | Gemini CLI | Cursor | Windsurf | Amazon Q | GitHub Copilot |
|-----------|-------------|--------------|------------|--------|----------|----------|----------------|
| **Config format** | Markdown + YAML frontmatter | TOML + Markdown + YAML | JSON + Markdown + YAML | MDC (Markdown + YAML) | Markdown + YAML | Markdown + JSON | Markdown + YAML |
| **Instruction file** | CLAUDE.md | AGENTS.md | GEMINI.md | .cursor/rules/*.mdc | .windsurf/rules/*.md | .amazonq/rules/*.md | .github/copilot-instructions.md |
| **Skills location** | .claude/skills/ | .codex/skills/ | .gemini/skills/ | .cursor/rules/ + .claude/skills/ | .windsurf/rules/ + skills/ | .amazonq/rules/ | .github/skills/ |
| **SKILL.md support** | ✅ Native (origin) | ✅ Full adoption | ✅ Full adoption | ✅ Supported | ✅ Supported | ❌ Not yet | ✅ Full adoption |
| **AGENTS.md support** | ❌ (prefers CLAUDE.md) | ✅ Native (origin) | ✅ Configurable | ✅ Full support | ✅ Full support | ❌ | ✅ Full support |
| **Discovery mechanism** | File scan → LLM selection | Directory walk + LLM selection | File scan + activate_skill tool | Glob match + model decision | Glob match + model decision | Auto-load all rules | applyTo globs + always-on |
| **Activation modes** | Auto, manual /slash, disable-model | Explicit ($), implicit (auto) | On-demand via activate_skill | Always, Auto, Agent, Manual, Legacy | Always On, Glob, Model, Manual | Always active | Always-on + path scoping |
| **Sub-agent support** | ✅ context:fork + agent types | ✅ Codex as MCP server | ✅ A2A remote agents | ❌ | ❌ | ✅ Custom agents (CLI) | ✅ Agent definitions |
| **Script execution** | ✅ scripts/ directory | ✅ scripts/ directory | ✅ Shell commands | ❌ Rules only | ❌ Rules only | ✅ Via agents | ✅ Hooks |
| **MCP support** | ✅ .mcp.json | ✅ config.toml | ✅ settings.json | ✅ Settings | ✅ mcp_config.json | ✅ .amazonq/mcp.json | ✅ Docker MCP |
| **Permission model** | Sandbox + allowlists + hooks | Sandbox + approval policies | Confirm + YOLO + sandbox | User approval | Cascade modes | Enterprise controls | Org-level policies |
| **Token/size limits** | ~5,000 tokens/SKILL.md recommended | project_doc_max_bytes configurable | No hard limit documented | Best practice: focused rules | Best practice: focused rules | No documented limit | ~1,000 lines per file |
| **Open standard** | Agent Skills (AAIF) | Agent Skills + AGENTS.md (AAIF) | Agent Skills + A2A | Supports both standards | Supports both standards | Proprietary rules | Supports both standards |

---

## 6. A universal skill format is already here

The feasibility question has been answered by the market: **Agent Skills (SKILL.md) IS the universal format**, adopted by every major platform. The remaining differences are narrower than expected.

### What's shared across all platforms

Every major coding agent now supports: **Markdown-based instructions** as the core content format, **YAML frontmatter** for metadata (name + description at minimum), **directory-based packaging** (skill directory with supporting files), **progressive disclosure** (metadata loaded first, full content on activation), **MCP for tool connectivity**, and **Git-friendly plain-text files** that version-control naturally.

### What remains platform-specific

The differences that persist are largely mechanical:

- **Storage paths**: `.claude/skills/` vs `.codex/skills/` vs `.gemini/skills/` vs `.cursor/rules/`
- **Extended frontmatter**: Claude adds `context`, `agent`, `model`; Codex adds `agents/openai.yaml`; Cursor uses `globs` and `alwaysApply`
- **Activation semantics**: Claude uses LLM-only routing; Cursor adds glob matching; Gemini uses an explicit `activate_skill` tool call
- **Instruction file names**: CLAUDE.md vs AGENTS.md vs GEMINI.md (though AGENTS.md is gaining universal adoption)
- **Hooks/lifecycle**: Claude's 13+ hook events are unique; other platforms have simpler or no hook systems
- **Frontmatter handling**: Claude Code ignores unknown YAML fields; Cursor requires specific fields — but both read the same Markdown body

### Could skills be transpiled across platforms?

Yes, and **tools already exist**. The most mature is **Rulesync** (`github.com/dyoshikawa/rulesync`, v5.4.0), which generates tool-native config files for **12+ agents** from a single `.rulesync/` source directory. **OpenSkills** (`github.com/numman-ali/openskills`) makes Claude Code's skill format work across any AGENTS.md-compatible agent. **Skillkit** provides cross-agent skill translation with a package manager model. The simplest approach — symlinking AGENTS.md to CLAUDE.md — works for many use cases.

However, **the need for transpilation is rapidly diminishing**. As platforms converge on SKILL.md, the core format requires no translation. Only storage paths and platform-specific extensions need adaptation, and most platforms already search multiple standard locations.

### Existing cross-platform projects

| Project | Approach | Platforms Supported |
|---------|----------|-------------------|
| Rulesync (npm) | Transpiler — single source → multiple outputs | 12+ agents including Claude, Codex, Cursor, Gemini, Copilot |
| OpenSkills (npm) | Universal loader — generates XML skill blocks in AGENTS.md | Any AGENTS.md-compatible agent |
| Skillkit | Package manager — cross-agent translation | 28+ agents |
| skills.sh | Distribution hub — one-command install | All SKILL.md-compatible agents |

---

## 7. Architecture for a multi-platform skill optimizer

### Three viable approaches

**Transpiler approach** (Rulesync model): Author skills once in a canonical format, compile to platform-specific outputs. Precedent: Sass→CSS, Terraform→provider configs. Best when platforms have genuinely different formats. Maintenance burden scales with number of target platforms × format drift rate.

**Adapter approach** (Oracle Agent Spec model): Define a shared core skill representation with thin runtime adapters per platform. Precedent: ONNX (train in PyTorch, run in TensorFlow). Best when the core representation is stable but execution environments differ. Lower maintenance but requires adapter updates when platforms change.

**Shared standard + extensions approach** (what's actually happening): Use SKILL.md as the single source format, with platform-specific frontmatter fields that each platform ignores if unrecognized. A thin deployment script copies skills to the correct platform directory. This is the lowest-maintenance approach because it leverages the industry convergence already underway.

### Recommended architecture

**The shared standard + extensions approach minimizes maintenance burden** because the industry has done the hard convergence work already. A practical multi-platform skill optimizer needs only three components:

1. **A deployment CLI** that copies SKILL.md directories to the correct platform paths (`.claude/skills/`, `.codex/skills/`, `.gemini/skills/`, etc.) — trivial shell script or npm package
2. **A frontmatter merger** that takes a base SKILL.md and overlays platform-specific fields from a `platforms/` directory (e.g., `platforms/claude.yaml` adds `context: fork`, `platforms/cursor.yaml` adds `globs`)
3. **An AGENTS.md generator** that produces project-level instruction files from skill metadata for platforms that don't natively scan SKILL.md directories

This is significantly simpler than a full transpiler because **95%+ of the skill content (the Markdown body) is identical across platforms**. Only metadata and deployment targets vary.

---

## 8. Risks, unknowns, and what to watch

**Standard governance stability** is the biggest risk. AAIF is two months old. The three co-founders (Anthropic, OpenAI, Block) are competitors. If governance fractures, standards could fork. The MCP precedent is encouraging — it has maintained coherence through rapid growth — but Agent Skills adoption is even faster and less battle-tested.

**Spec evolution pace** creates compatibility risk. Claude Code already extends SKILL.md well beyond the open spec (context forking, subagents, hooks integration). If other platforms add incompatible extensions, the "universal" format could balkanize into dialects. The spec's `metadata` field (arbitrary key-value pairs) is designed as an escape valve, but there's no formal extension registry.

**Progressive disclosure semantics differ**. Claude Code uses pure LLM reasoning for skill selection; Cursor uses glob matching; Gemini uses an explicit tool call. A skill optimized for one discovery mechanism may underperform on another. Description quality becomes the critical portable element — write descriptions that work well for both LLM selection and keyword matching.

**Security model fragmentation** is notable. Claude Code's sandbox is the most mature (OS-level isolation with Seatbelt/bubblewrap). Codex matches this for cloud tasks. Gemini CLI defaults to **no sandbox** (a red warning is displayed). There is no standard for declaring a skill's security requirements — a skill that needs network access works differently on each platform.

**Key unknowns** include: whether AAIF will accept Agent Skills as a formal project (currently only MCP, AGENTS.md, and goose are founding projects); how Swarms/multi-agent orchestration will evolve across platforms; whether the 160,000+ skills on marketplaces maintain quality standards; and whether Claude Code will adopt AGENTS.md support natively or continue requiring CLAUDE.md.

---

## Conclusion

The agent skill landscape in early 2026 has settled into a remarkably clear architecture: **Agent Skills (SKILL.md) for portable capabilities**, **AGENTS.md for project instructions**, and **MCP for tool connectivity** — all governed by the Linux Foundation's AAIF. The competitive frontier has shifted from format lock-in to execution quality: which platform's LLM best selects and follows skills, which sandbox is most secure, and which ecosystem surfaces the best community-contributed skills.

For anyone building a multi-platform skill system today, the strategic move is to **write skills in the Agent Skills format, deploy to platform-specific paths with a thin CLI, and use AGENTS.md as the universal instruction fallback**. Tools like Rulesync and OpenSkills already handle this. The era of proprietary agent configuration formats lasted roughly 18 months — from mid-2024 (Cursor's .cursorrules) to December 2025 (AAIF formation). What remains is the hard work of writing excellent skills and building the quality infrastructure (testing, linting, versioning) that a 160,000-skill ecosystem demands.