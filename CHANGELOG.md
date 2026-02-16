# Changelog

## v1.0.0 — Initial Release

### Features

- **Skill Forge orchestrator** — Tier 4 skill with routing table, 6 sub-skills, 4 agents, 4 scripts
- **Plan** — Architecture design with complexity tier detection (1-4), sub-skill decomposition, and file structure planning
- **Build** — Full skill scaffolding with SKILL.md generation, frontmatter writing, sub-skills, scripts, references, and agents
- **Review** — Quality auditing with 0-100 health score across 6 categories (structure, frontmatter, description, body, scripts, agents)
- **Evolve** — Skill improvement based on feedback, triggering issues, and testing results
- **Publish** — Packaging as `.skill` ZIP files with install script generation
- **Convert** — Multi-platform conversion to OpenAI Codex, Google Gemini CLI, Google Antigravity, and Cursor
- **10 reference files** — Comprehensive knowledge base covering anatomy, patterns, frontmatter spec, description guide, testing, 3-layer architecture, tools, hooks, activation, and platform specs
- **4 execution scripts** — `init_skill.py` (scaffold), `validate_skill.py` (validate), `package_skill.py` (package), `convert_skill.py` (convert)
- **4 agent definitions** — Architect, Writer, Validator, and Converter subagents for parallel delegation
- **4 skill templates** — Tier 1 (minimal), Tier 2 (workflow), Tier 3 (multi-skill), Tier 4 (ecosystem)
- **Progressive disclosure** — 3-level loading (frontmatter always, instructions on activation, references on demand)
- **Agent Skills standard** — Full compliance with the open standard at agentskills.io
