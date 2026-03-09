#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "Uninstalling skill-forge..."

    # Remove main skill
    rm -rf "${HOME}/.claude/skills/skill-forge"

    # Remove sub-skills
    for skill in skill-forge-build skill-forge-convert skill-forge-evolve skill-forge-plan skill-forge-publish skill-forge-review; do
        rm -rf "${HOME}/.claude/skills/${skill}"
    done

    # Remove agents
    for agent in skill-forge-architect skill-forge-writer skill-forge-validator skill-forge-converter; do
        rm -f "${HOME}/.claude/agents/${agent}.md"
    done

    echo "skill-forge uninstalled."
    echo "Restart Claude Code to complete removal."
}

main "$@"
