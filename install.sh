#!/usr/bin/env bash
# Install Skill Forge -- Ultimate Claude Code Skill Creator
# Usage: bash install.sh [--uninstall]
#
# Installs:
# - Main skill (skill-forge) to ~/.claude/skills/
# - Sub-skills (skill-forge-*) to ~/.claude/skills/
# - Agent definitions to ~/.claude/agents/

set -euo pipefail

SKILL_DIR="$HOME/.claude/skills"
AGENT_DIR="$HOME/.claude/agents"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    if [ $? -ne 0 ]; then
        echo ""
        echo "  [ERR] Installation failed. No partial files left."
    fi
}
trap cleanup EXIT

uninstall() {
    echo "========================================="
    echo "  Skill Forge Uninstaller"
    echo "========================================="
    echo ""

    local removed=0

    # Remove main skill
    if [ -d "$SKILL_DIR/skill-forge" ]; then
        rm -rf "$SKILL_DIR/skill-forge"
        echo "  [OK] Removed: skill-forge"
        removed=$((removed + 1))
    fi

    # Remove sub-skills
    for skill_dir in "$SKILL_DIR"/skill-forge-*/; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            rm -rf "$skill_dir"
            echo "  [OK] Removed: $skill_name"
            removed=$((removed + 1))
        fi
    done

    # Remove agents
    for agent_file in "$AGENT_DIR"/skill-forge-*.md; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file")
            rm -f "$agent_file"
            echo "  [OK] Removed: agent $agent_name"
            removed=$((removed + 1))
        fi
    done

    echo ""
    echo "  Removed $removed items."
    echo ""
    exit 0
}

main() {
    # Handle --uninstall flag
    if [ "${1:-}" = "--uninstall" ]; then
        uninstall
    fi

    echo "========================================="
    echo "  Skill Forge Installer"
    echo "  Ultimate Claude Code Skill Creator"
    echo "========================================="
    echo ""

    # Create directories
    mkdir -p "$SKILL_DIR" "$AGENT_DIR"

    # Install main skill
    if [ -d "$SCRIPT_DIR/skill-forge" ]; then
        cp -r "$SCRIPT_DIR/skill-forge" "$SKILL_DIR/"
        echo "  [OK] Installed: skill-forge (main orchestrator)"
    else
        echo "  [ERR] skill-forge/ directory not found"
        exit 1
    fi

    # Install sub-skills
    INSTALLED_SKILLS=0
    for skill_dir in "$SCRIPT_DIR/skills"/skill-forge-*/; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            cp -r "$skill_dir" "$SKILL_DIR/"
            echo "  [OK] Installed: $skill_name"
            INSTALLED_SKILLS=$((INSTALLED_SKILLS + 1))
        fi
    done

    # Install agents
    INSTALLED_AGENTS=0
    if [ -d "$SCRIPT_DIR/agents" ]; then
        for agent_file in "$SCRIPT_DIR/agents"/skill-forge-*.md; do
            if [ -f "$agent_file" ]; then
                cp "$agent_file" "$AGENT_DIR/"
                agent_name=$(basename "$agent_file")
                echo "  [OK] Installed: agent $agent_name"
                INSTALLED_AGENTS=$((INSTALLED_AGENTS + 1))
            fi
        done
    fi

    echo ""
    echo "========================================="
    echo "  Installation Complete!"
    echo "========================================="
    echo ""
    echo "  Main skill:  1"
    echo "  Sub-skills:  $INSTALLED_SKILLS"
    echo "  Agents:      $INSTALLED_AGENTS"
    echo ""
    echo "  Get started:"
    echo "    /skill-forge          Interactive wizard"
    echo "    /skill-forge plan     Design a new skill"
    echo "    /skill-forge build    Scaffold a skill"
    echo "    /skill-forge review   Audit a skill"
    echo "    /skill-forge convert  Convert to other platforms"
    echo ""
    echo "  Uninstall:"
    echo "    bash install.sh --uninstall"
    echo ""
}

main "$@"
