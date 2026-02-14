# Tools Reference for Skill Creators

Complete list of tool names for `allowed-tools` frontmatter and permission patterns.

## Core Tools

| Tool | `allowed-tools` Name | Purpose |
|------|---------------------|---------|
| Read | `Read` | Read files (text, images, PDFs, notebooks) |
| Write | `Write` | Create or overwrite files |
| Edit | `Edit` | Exact string replacement in files |
| Bash | `Bash` | Execute shell commands |
| Glob | `Glob` | Find files by pattern |
| Grep | `Grep` | Search file contents (ripgrep) |
| WebFetch | `WebFetch` | Fetch and process web content |
| WebSearch | `WebSearch` | Search the web |
| Task | `Task` | Spawn subagents |
| NotebookEdit | `NotebookEdit` | Edit Jupyter notebook cells |
| Skill | `Skill(name)` | Invoke other skills |
| TodoWrite | `TodoWrite` | Task list management |
| AskUserQuestion | `AskUserQuestion` | Prompt user for input |
| LSP | `LSP` | Language server queries |
| MCPSearch | `MCPSearch` | Search MCP tool descriptions |
| TaskOutput | `TaskOutput` | Read background task output |
| TaskStop | `TaskStop` | Stop running tasks |

## Bash Permission Patterns

Restrict Bash access with patterns in `allowed-tools`:

| Pattern | Matches |
|---------|---------|
| `Bash` | All commands |
| `Bash(git:*)` | Git commands only |
| `Bash(npm:*)` | npm commands only |
| `Bash(npm test:*)` | npm test only |
| `Bash(npm *)` | npm with any subcommand |
| `Bash(* install)` | Commands ending with "install" |
| `Bash(git * main)` | Git commands containing "main" |
| `Bash(*)` | Equivalent to `Bash` |

## Task Permission Patterns

Restrict which subagents can be spawned:

| Pattern | Matches |
|---------|---------|
| `Task` | All subagent types |
| `Task(AgentName)` | Only the named agent |

## Skill Permission Patterns

| Pattern | Matches |
|---------|---------|
| `Skill(name)` | Specific skill only |
| `Skill(name *)` | Skill with any arguments |

## MCP Tool Naming

MCP tools follow the pattern `mcp__<server>__<tool>`:

| Pattern | Matches |
|---------|---------|
| `mcp__server__tool` | Specific MCP tool |
| `mcp__server__*` | All tools from server |
| `mcp__plugin_name_server__*` | Plugin-provided tools |

## Wildcard

Use `"*"` in `allowed-tools` to grant access to ALL tools (use sparingly).

## Key Tool Capabilities

### Read
- Up to 2000 lines by default, with offset/limit for large files
- Reads images visually (multimodal), PDFs (use `pages` for >10 pages)
- Reads Jupyter notebooks with all cell outputs

### Write
- Requires file to have been Read first if it exists
- Creates intermediate directories
- Blocked from writing to `.claude/skills` in sandbox mode

### Edit
- Requires file to have been Read first
- `old_string` must be unique (or use `replace_all: true`)
- Preserves exact indentation

### Bash
- Working directory persists between calls; shell state does not
- Default timeout: 2 minutes (max 10 minutes)
- `run_in_background: true` for async execution
- Large outputs saved to disk (not truncated)

### WebFetch
- Converts HTML to markdown, processes with AI
- FAILS for authenticated/private URLs
- 15-minute cache for repeated access

### WebSearch
- Domain filtering via `allowed_domains` / `blocked_domains`
- Only available in the US

### Task (Subagents)
- Spawns independent subagent with own context window
- Custom agent types from `agents/` directory
- Background support with `run_in_background`

## Built-in Agent Types

| Agent | Model | Purpose |
|-------|-------|---------|
| `Explore` | Haiku | Fast read-only code exploration |
| `Plan` | Inherit | Planning and analysis |
| `general-purpose` | Inherit | Full task delegation |
| `Bash` | Inherit | Command execution |

## MCP Server Types

| Type | Transport | Best For |
|------|-----------|----------|
| stdio | Process stdin/stdout | Local tools, NPM packages |
| SSE | HTTP + Server-Sent Events | Cloud services, OAuth |
| HTTP | REST request/response | REST APIs, stateless |
| WebSocket | Persistent bidirectional | Real-time, low-latency |

Configure in `.mcp.json`, `settings.json`, or plugin `mcpServers` field.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Override file read token limit |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Override skill character budget |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Enable agent teams |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | Disable background tasks |
