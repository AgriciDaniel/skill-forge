# Skill Forge -- Ultimate Claude Code Skill Creator

## Project Overview

This repository contains **Skill Forge**, a Tier 4 Claude Code skill for creating,
reviewing, evolving, and publishing other Claude Code skills. It follows the Agent
Skills open standard and the 3-layer architecture (directive, orchestration, execution).

## Architecture

```
claude-skill/
  CLAUDE.md                          # This file (project instructions)
  skill-forge/                       # Main orchestrator skill (Tier 4)
    SKILL.md                         # Entry point, routing table, core rules
    references/                      # On-demand knowledge files (9 files)
      anatomy.md                     # Skill file structure, naming, agent format
      patterns.md                    # Proven workflow patterns
      frontmatter-spec.md           # YAML frontmatter specification (skills)
      description-guide.md          # Writing effective descriptions
      testing-guide.md              # Testing methodology
      pro-agent.md                  # 3-layer architecture deep dive
      tools-reference.md            # Tool names, permission patterns, MCP
      hooks-reference.md            # Hook events, types, quality gates
      skills-activation.md          # Skill discovery, activation, features
    scripts/                         # Deterministic execution scripts
      init_skill.py                 # Scaffold new skills
      validate_skill.py             # Validate skill structure
      package_skill.py              # Package for distribution
    assets/
      templates/                     # Skill templates by tier
        minimal.md                  # Tier 1: single SKILL.md
        workflow.md                 # Tier 2: SKILL.md + scripts
        multi-skill.md             # Tier 3: orchestrator + sub-skills
        ecosystem.md               # Tier 4: full ecosystem
  skills/                            # Sub-skills
    skill-forge-plan/SKILL.md       # Architecture and design planning
    skill-forge-build/SKILL.md      # Scaffold and generate skills
    skill-forge-review/SKILL.md     # Audit and validate skills
    skill-forge-evolve/SKILL.md     # Improve skills from feedback
    skill-forge-publish/SKILL.md    # Package and distribute skills
  agents/                            # Subagent definitions
    skill-forge-architect.md        # Architecture design agent
    skill-forge-writer.md           # SKILL.md content writer agent
    skill-forge-validator.md        # Validation agent
  install.sh                         # Installation script
```

## Key Principles

1. **Progressive Disclosure**: Metadata always loaded, instructions on activation, resources on demand
2. **Description is King**: The YAML description field determines when skills activate
3. **3-Layer Architecture**: Directives (SKILL.md) + Orchestration (Claude) + Execution (scripts)
4. **Self-Annealing**: Learn from failures, update skills with discoveries
5. **Simplicity First**: Start with Tier 1, evolve to higher tiers only when needed

## Development Rules

- Test with `python skill-forge/scripts/validate_skill.py <path>` after changes
- Keep SKILL.md files under 500 lines / 5000 tokens
- Reference files should be focused and under 200 lines
- Scripts must have docstrings, CLI interface, JSON output
- Follow kebab-case naming for all skill directories
- Never put README.md inside skill folders

## Commands

| Command | Purpose |
|---------|---------|
| `/skill-forge` | Interactive skill creation wizard |
| `/skill-forge plan` | Design skill architecture |
| `/skill-forge build` | Scaffold and generate skill files |
| `/skill-forge review` | Audit existing skill quality |
| `/skill-forge evolve` | Improve skill from feedback |
| `/skill-forge publish` | Package for distribution |

## Related Skills Built with Skill Forge

### Skool Skill Ecosystem (Tier 4)
- **Source**: `~/Desktop/claude-skool/` (25 files: 1 main + 7 sub-skills + 4 agents + 4 references + 6 templates + 2 scripts)
- **Installed at**: `~/.claude/skills/skool*/`
- **Communities**: ai-marketing-hub (free), ai-marketing-hub-pro (paid $59-79/mo)
- **MCP Server**: `~/Workflows/skool-mcp/` (FastMCP + Playwright, provides live Skool data tools)
- **Live Data Snapshots**: `~/Desktop/claude-skool/data/` (pro-community-snapshot.md, free-community-snapshot.md)
- **MCP Tools**: `skool_login`, `skool_get_community`, `skool_list_courses`, `skool_get_course`, `skool_get_lesson`, `skool_get_members`, `skool_get_leaderboard`, `skool_get_feed`
