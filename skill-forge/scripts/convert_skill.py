#!/usr/bin/env python3
"""
Purpose: Convert Claude Code skills to work on OpenAI Codex, Gemini CLI, Antigravity, and Cursor.
Input: Path to a skill directory, target platforms, optional output directory
Output: JSON conversion report with generated files and compatibility scores
Usage: python scripts/convert_skill.py /path/to/skill --target codex,gemini,antigravity,cursor [--output dist/] [--dry-run] [--include-mcp]
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


# --- Field Classification ---

PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "argument-hint"}

ADAPTABLE_FIELDS = {
    "allowed-tools": {
        "codex": "keep",
        "gemini": "strip",
        "antigravity": "strip",
        "cursor": "strip",
    },
    "disable-model-invocation": {
        "codex": "move_to_openai_yaml",
        "gemini": "strip",
        "antigravity": "strip",
        "cursor": "strip",
    },
}

CLAUDE_ONLY_FIELDS = {
    "context": "No equivalent. Subagent isolation is Claude Code specific.",
    "agent": "No equivalent. Agent delegation is Claude Code specific.",
    "hooks": "No equivalent. Lifecycle hooks are Claude Code specific.",
    "model": "No equivalent. Model selection is Claude Code specific.",
    "user-invocable": "Skills are always discoverable on other platforms.",
    "skills": "No equivalent. Sub-skill references are Claude Code specific.",
    "memory": "No equivalent. Persistent memory is Claude Code specific.",
}

# Platform skill paths
PLATFORM_PATHS = {
    "codex": {"project": ".agents/skills", "user": "~/.agents/skills"},
    "gemini": {"project": ".gemini/skills", "user": "~/.gemini/skills"},
    "antigravity": {"project": ".agent/skills", "user": "~/.gemini/antigravity/skills"},
    "cursor": {"project": ".cursor/skills", "user": "~/.cursor/skills"},
}

# Platform instruction files
PLATFORM_INSTRUCTION_FILES = {
    "codex": "AGENTS.md",
    "gemini": "GEMINI.md",
    "antigravity": "GEMINI.md",
    "cursor": "rules",  # .cursor/rules/<name>.mdc
}

# MCP config file names per platform
PLATFORM_MCP_FILES = {
    "codex": "config.toml",
    "gemini": "settings.json",
    "antigravity": "mcp_config.json",
    "cursor": "mcp.json",
}


# --- Frontmatter Parsing (reused from validate_skill.py) ---

def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    """Parse YAML frontmatter from SKILL.md content.

    Returns (frontmatter_dict, body, errors).
    Uses basic parsing to avoid PyYAML dependency.
    """
    errors: list[str] = []

    if not content.startswith('---'):
        return None, content, ["Missing opening '---' delimiter"]

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content, ["Missing closing '---' delimiter"]

    yaml_text = parts[1].strip()
    body = parts[2].strip()

    if not yaml_text:
        return None, body, ["Empty frontmatter"]

    frontmatter: dict[str, Any] = {}
    current_key = ""
    current_value = ""
    in_multiline = False
    in_list = False
    current_list: list[str] = []

    for line in yaml_text.split('\n'):
        stripped = line.strip()

        if in_multiline:
            if stripped and not re.match(r'^[a-z_-]+:', stripped):
                current_value += " " + stripped
                continue
            else:
                frontmatter[current_key] = current_value.strip()
                in_multiline = False

        if in_list:
            if stripped.startswith('- '):
                current_list.append(stripped[2:].strip())
                continue
            else:
                frontmatter[current_key] = current_list
                in_list = False
                current_list = []

        match = re.match(r'^([a-z_-]+):\s*(.*)', stripped)
        if match:
            current_key = match.group(1)
            value = match.group(2).strip()

            if value == '>':
                in_multiline = True
                current_value = ""
            elif value == '|':
                in_multiline = True
                current_value = ""
            elif value == '':
                in_list = True
                current_list = []
            else:
                frontmatter[current_key] = value.strip('"').strip("'")

    if in_multiline:
        frontmatter[current_key] = current_value.strip()
    if in_list and current_list:
        frontmatter[current_key] = current_list

    return frontmatter, body, errors


# --- Tier Detection ---

def detect_skill_tier(skill_path: Path) -> int:
    """Detect skill complexity tier (1-4) from directory structure."""
    has_scripts = (skill_path / "scripts").is_dir()
    has_references = (skill_path / "references").is_dir()
    has_agents = False
    has_sub_skills = False

    # Check parent directory for agents/ and skills/ folders
    parent = skill_path.parent
    skill_name = skill_path.name

    agents_dir = parent / "agents"
    if agents_dir.is_dir():
        has_agents = any(agents_dir.glob(f"{skill_name}-*.md"))

    skills_dir = parent / "skills"
    if skills_dir.is_dir():
        has_sub_skills = any(skills_dir.glob(f"{skill_name}-*/"))

    if has_agents and has_sub_skills:
        return 4  # Full ecosystem
    if has_sub_skills:
        return 3  # Multi-skill orchestrator
    if has_scripts or has_references:
        return 2  # Skill + scripts/references
    return 1  # Single skill


# --- Field Classification ---

def classify_frontmatter_fields(fm: dict[str, Any]) -> dict[str, list[str]]:
    """Classify frontmatter fields into portable, adaptable, and claude_only."""
    result: dict[str, list[str]] = {
        "portable": [],
        "adaptable": [],
        "claude_only": [],
    }

    for key in fm:
        if key in PORTABLE_FIELDS:
            result["portable"].append(key)
        elif key in ADAPTABLE_FIELDS:
            result["adaptable"].append(key)
        elif key in CLAUDE_ONLY_FIELDS:
            result["claude_only"].append(key)
        else:
            result["claude_only"].append(key)

    return result


def calculate_compatibility_score(classification: dict[str, list[str]]) -> int:
    """Calculate platform compatibility score (0-100)."""
    total = sum(len(v) for v in classification.values())
    if total == 0:
        return 100

    portable_count = len(classification["portable"])
    adaptable_count = len(classification["adaptable"])
    claude_only_count = len(classification["claude_only"])

    # Portable fields = full weight, adaptable = half weight, claude_only = 0
    score = ((portable_count * 1.0 + adaptable_count * 0.5) / total) * 100
    return min(100, max(0, round(score)))


# --- Body Content Adaptation ---

# Patterns to find and replace in skill body text per platform
BODY_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "codex": [
        (r'~/\.claude/skills/', '~/.agents/skills/'),
        (r'\.claude/skills/', '.agents/skills/'),
        (r'~/\.claude/', '~/.agents/'),
        (r'\.claude/', '.agents/'),
        (r'CLAUDE\.md', 'AGENTS.md'),
    ],
    "gemini": [
        (r'~/\.claude/skills/', '~/.gemini/skills/'),
        (r'\.claude/skills/', '.gemini/skills/'),
        (r'~/\.claude/', '~/.gemini/'),
        (r'\.claude/', '.gemini/'),
        (r'CLAUDE\.md', 'GEMINI.md'),
    ],
    "antigravity": [
        (r'~/\.claude/skills/', '~/.gemini/antigravity/skills/'),
        (r'\.claude/skills/', '.agent/skills/'),
        (r'~/\.claude/', '~/.gemini/antigravity/'),
        (r'\.claude/', '.agent/'),
        (r'CLAUDE\.md', 'GEMINI.md'),
        (r'\./scripts/', '{{SKILL_PATH}}/scripts/'),
        (r'\./references/', '{{SKILL_PATH}}/references/'),
    ],
    "cursor": [
        (r'~/\.claude/skills/', '~/.cursor/skills/'),
        (r'\.claude/skills/', '.cursor/skills/'),
        (r'~/\.claude/', '~/.cursor/'),
        (r'\.claude/', '.cursor/'),
        (r'CLAUDE\.md', '.cursor/rules/'),
    ],
}

# Patterns that can't be auto-replaced -- just warn about them
BODY_WARNING_PATTERNS: list[tuple[str, str]] = [
    (r'`/[a-z][\w-]+(?:\s+[a-z][\w-]+)*`', 'Slash command syntax is Claude Code specific. Codex uses $mention, Gemini uses description-based activation.'),
    (r'\bTask\s+tool\b', 'Task tool (subagent delegation) is Claude Code specific. No direct equivalent on other platforms.'),
    (r'\bspawn\s+(?:a\s+)?subagent', 'Subagent spawning is Claude Code specific.'),
    (r'\bcontext:\s*fork\b', 'Forked context is Claude Code specific.'),
    (r'\bhooks?\s*:', 'Lifecycle hooks are Claude Code specific.'),
]


def adapt_body_content(body: str, target: str) -> tuple[str, list[str]]:
    """Adapt skill body content for a target platform.

    Replaces Claude-specific paths, file references, and config names.
    Returns (adapted_body, warnings) where warnings list things that
    need manual review.
    """
    adapted = body
    warnings: list[str] = []

    # Apply automatic replacements
    replacements = BODY_REPLACEMENTS.get(target, [])
    for pattern, replacement in replacements:
        new_text = re.sub(pattern, replacement, adapted)
        if new_text != adapted:
            warnings.append(f"Auto-replaced '{pattern.replace(chr(92), '')}' -> '{replacement}' in body text.")
        adapted = new_text

    # Scan for patterns that need manual attention
    for pattern, message in BODY_WARNING_PATTERNS:
        matches = re.findall(pattern, body)
        if matches:
            unique = list(set(matches))[:3]  # Show up to 3 examples
            examples = ", ".join(f"'{m.strip()}'" for m in unique)
            warnings.append(f"Manual review needed: {message} Found: {examples}")

    return adapted, warnings


# --- Frontmatter Generation ---

def strip_claude_fields(fm: dict[str, Any], target: str) -> tuple[dict[str, Any], list[str]]:
    """Remove Claude-only and platform-incompatible fields. Returns (cleaned_fm, warnings)."""
    cleaned: dict[str, Any] = {}
    warnings: list[str] = []

    for key, value in fm.items():
        if key in PORTABLE_FIELDS:
            cleaned[key] = value
        elif key in ADAPTABLE_FIELDS:
            action = ADAPTABLE_FIELDS[key].get(target, "strip")
            if action == "keep":
                cleaned[key] = value
            elif action == "move_to_openai_yaml":
                warnings.append(f"Field '{key}' moved to openai.yaml (Codex platform extension)")
            else:
                workaround = ""
                if key == "allowed-tools":
                    workaround = "All tools available by default on this platform."
                warnings.append(f"Field '{key}' removed: not supported on {target}. {workaround}".strip())
        elif key in CLAUDE_ONLY_FIELDS:
            warnings.append(f"Field '{key}' removed: {CLAUDE_ONLY_FIELDS[key]}")
        else:
            warnings.append(f"Field '{key}' removed: unknown field, may be Claude Code specific.")

    return cleaned, warnings


def generate_frontmatter_text(fm: dict[str, Any]) -> str:
    """Generate YAML frontmatter text from a dict."""
    lines = ["---"]

    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, str) and (len(value) > 80 or '\n' in value):
            lines.append(f"{key}: >")
            # Wrap long descriptions
            words = value.split()
            current_line = "  "
            for word in words:
                if len(current_line) + len(word) + 1 > 80:
                    lines.append(current_line)
                    current_line = "  " + word
                else:
                    current_line += (" " if len(current_line) > 2 else "") + word
            if current_line.strip():
                lines.append(current_line)
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")

    lines.append("---")
    return "\n".join(lines)


# --- Platform-Specific Generators ---

def generate_openai_yaml(fm: dict[str, Any]) -> str:
    """Generate Codex openai.yaml platform extension."""
    name = fm.get("name", "skill")
    display_name = name.replace("-", " ").title()

    lines = [
        "interface:",
        f'  display_name: "{display_name}"',
        "",
        "policy:",
    ]

    # Map disable-model-invocation to allow_implicit_invocation (inverted)
    disable_invocation = fm.get("disable-model-invocation", "false")
    allow_implicit = "false" if disable_invocation == "true" else "true"
    lines.append(f"  allow_implicit_invocation: {allow_implicit}")

    return "\n".join(lines) + "\n"


def generate_instruction_file(fm: dict[str, Any], body: str, platform: str) -> str:
    """Generate AGENTS.md or GEMINI.md from skill content.

    Extracts the body content and re-titles it to avoid duplicate H1 headings.
    Demotes body headings if they conflict with the generated structure.
    """
    name = fm.get("name", "skill")
    description = fm.get("description", "")
    display_name = name.replace("-", " ").title()

    lines = [
        f"# {display_name}",
        "",
        description,
        "",
    ]

    if body:
        # Strip any leading H1 from body to avoid duplicate top-level heading
        body_lines = body.split('\n')
        start_idx = 0
        for i, line in enumerate(body_lines):
            stripped = line.strip()
            if stripped.startswith('# ') and not stripped.startswith('## '):
                # Skip this H1 -- we already have one
                start_idx = i + 1
                # Also skip blank lines right after the removed H1
                while start_idx < len(body_lines) and not body_lines[start_idx].strip():
                    start_idx += 1
                break
            elif stripped:
                # First non-empty line isn't H1, keep everything
                break

        trimmed_body = '\n'.join(body_lines[start_idx:]).strip()
        if trimmed_body:
            lines.append(trimmed_body)

    return "\n".join(lines) + "\n"


def generate_codex_output(
    skill_path: Path,
    fm: dict[str, Any],
    body: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Generate Codex-compatible skill output."""
    cleaned_fm, warnings = strip_claude_fields(fm, "codex")
    manual_steps: list[str] = []

    # Adapt body content for Codex
    adapted_body, body_warnings = adapt_body_content(body, "codex")
    warnings.extend(body_warnings)

    skill_name = fm.get("name", skill_path.name)
    target_dir = output_dir / "codex" / skill_name

    # Create directory structure
    target_dir.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []

    # Generate SKILL.md with cleaned frontmatter and adapted body
    skill_md_content = generate_frontmatter_text(cleaned_fm) + "\n\n" + adapted_body
    (target_dir / "SKILL.md").write_text(skill_md_content)
    files_created.append(f"{skill_name}/SKILL.md")

    # Generate openai.yaml
    agents_dir = target_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    openai_yaml = generate_openai_yaml(fm)
    (agents_dir / "openai.yaml").write_text(openai_yaml)
    files_created.append(f"{skill_name}/agents/openai.yaml")

    # Generate AGENTS.md with adapted body
    agents_md = generate_instruction_file(fm, adapted_body, "codex")
    (target_dir / "AGENTS.md").write_text(agents_md)
    files_created.append(f"{skill_name}/AGENTS.md")

    # Copy scripts if present
    src_scripts = skill_path / "scripts"
    if src_scripts.is_dir():
        dst_scripts = target_dir / "scripts"
        shutil.copytree(src_scripts, dst_scripts, dirs_exist_ok=True)
        for f in dst_scripts.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "codex")))

    # Copy references if present
    src_refs = skill_path / "references"
    if src_refs.is_dir():
        dst_refs = target_dir / "references"
        shutil.copytree(src_refs, dst_refs, dirs_exist_ok=True)
        for f in dst_refs.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "codex")))

    # Tier 3-4 notes
    tier = detect_skill_tier(skill_path)
    if tier >= 3:
        manual_steps.append("Routing table uses Claude Code slash commands. Adapt to Codex $mention syntax.")
    if tier >= 4:
        manual_steps.append("Subagent delegation (Task tool) has no direct Codex equivalent. Consider breaking into separate skills.")

    classification = classify_frontmatter_fields(fm)

    return {
        "output_dir": str(target_dir),
        "files_created": files_created,
        "compatibility_score": calculate_compatibility_score(classification),
        "warnings": warnings,
        "manual_steps": manual_steps,
    }


def generate_gemini_output(
    skill_path: Path,
    fm: dict[str, Any],
    body: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Generate Gemini CLI compatible skill output."""
    cleaned_fm, warnings = strip_claude_fields(fm, "gemini")
    manual_steps: list[str] = []

    # Adapt body content for Gemini
    adapted_body, body_warnings = adapt_body_content(body, "gemini")
    warnings.extend(body_warnings)

    skill_name = fm.get("name", skill_path.name)
    target_dir = output_dir / "gemini" / skill_name

    target_dir.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []

    # Generate SKILL.md with cleaned frontmatter and adapted body
    skill_md_content = generate_frontmatter_text(cleaned_fm) + "\n\n" + adapted_body
    (target_dir / "SKILL.md").write_text(skill_md_content)
    files_created.append(f"{skill_name}/SKILL.md")

    # Generate GEMINI.md with adapted body
    gemini_md = generate_instruction_file(fm, adapted_body, "gemini")
    (target_dir / "GEMINI.md").write_text(gemini_md)
    files_created.append(f"{skill_name}/GEMINI.md")

    # Copy scripts if present
    src_scripts = skill_path / "scripts"
    if src_scripts.is_dir():
        dst_scripts = target_dir / "scripts"
        shutil.copytree(src_scripts, dst_scripts, dirs_exist_ok=True)
        for f in dst_scripts.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "gemini")))

    # Copy references if present
    src_refs = skill_path / "references"
    if src_refs.is_dir():
        dst_refs = target_dir / "references"
        shutil.copytree(src_refs, dst_refs, dirs_exist_ok=True)
        for f in dst_refs.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "gemini")))

    tier = detect_skill_tier(skill_path)
    if tier >= 3:
        manual_steps.append("Routing table uses Claude Code slash commands. Gemini relies on description-based activation.")
    if tier >= 4:
        manual_steps.append("Subagent delegation (Task tool) has no Gemini CLI equivalent.")

    classification = classify_frontmatter_fields(fm)

    return {
        "output_dir": str(target_dir),
        "files_created": files_created,
        "compatibility_score": calculate_compatibility_score(classification),
        "warnings": warnings,
        "manual_steps": manual_steps,
    }


def generate_antigravity_output(
    skill_path: Path,
    fm: dict[str, Any],
    body: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Generate Antigravity compatible skill output."""
    cleaned_fm, warnings = strip_claude_fields(fm, "antigravity")
    manual_steps: list[str] = []

    # Adapt body content for Antigravity
    adapted_body, body_warnings = adapt_body_content(body, "antigravity")
    warnings.extend(body_warnings)

    skill_name = fm.get("name", skill_path.name)
    target_dir = output_dir / "antigravity" / skill_name

    target_dir.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []

    # Generate SKILL.md (name is optional on Antigravity but we keep it) with adapted body
    skill_md_content = generate_frontmatter_text(cleaned_fm) + "\n\n" + adapted_body
    (target_dir / "SKILL.md").write_text(skill_md_content)
    files_created.append(f"{skill_name}/SKILL.md")

    # Generate GEMINI.md with adapted body
    gemini_md = generate_instruction_file(fm, adapted_body, "antigravity")
    (target_dir / "GEMINI.md").write_text(gemini_md)
    files_created.append(f"{skill_name}/GEMINI.md")

    # Copy scripts if present
    src_scripts = skill_path / "scripts"
    if src_scripts.is_dir():
        dst_scripts = target_dir / "scripts"
        shutil.copytree(src_scripts, dst_scripts, dirs_exist_ok=True)
        for f in dst_scripts.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "antigravity")))

    # Copy references if present
    src_refs = skill_path / "references"
    if src_refs.is_dir():
        dst_refs = target_dir / "references"
        shutil.copytree(src_refs, dst_refs, dirs_exist_ok=True)
        for f in dst_refs.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "antigravity")))

    tier = detect_skill_tier(skill_path)
    if tier >= 3:
        manual_steps.append("Routing table is Claude Code specific. Antigravity uses description-based activation.")
    if tier >= 4:
        manual_steps.append("Subagent delegation (Task tool) has no Antigravity equivalent.")

    classification = classify_frontmatter_fields(fm)

    return {
        "output_dir": str(target_dir),
        "files_created": files_created,
        "compatibility_score": calculate_compatibility_score(classification),
        "warnings": warnings,
        "manual_steps": manual_steps,
    }


def generate_cursor_rule(fm: dict[str, Any], body: str) -> str:
    """Generate a .cursor/rules/<name>.mdc rule file.

    Cursor rules use a 3-field YAML frontmatter: description, globs, alwaysApply.
    """
    description = fm.get("description", "")
    # Escape double quotes to produce valid YAML
    escaped_description = description.replace('"', '\\"')
    lines = [
        "---",
        f"description: \"{escaped_description}\"",
        "alwaysApply: false",
        "---",
        "",
    ]

    if body:
        # Strip any leading H1 from body
        body_lines = body.split('\n')
        start_idx = 0
        for i, line in enumerate(body_lines):
            stripped = line.strip()
            if stripped.startswith('# ') and not stripped.startswith('## '):
                start_idx = i + 1
                while start_idx < len(body_lines) and not body_lines[start_idx].strip():
                    start_idx += 1
                break
            elif stripped:
                break
        trimmed_body = '\n'.join(body_lines[start_idx:]).strip()
        if trimmed_body:
            lines.append(trimmed_body)

    return "\n".join(lines) + "\n"


def generate_cursor_output(
    skill_path: Path,
    fm: dict[str, Any],
    body: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Generate Cursor-compatible skill output."""
    cleaned_fm, warnings = strip_claude_fields(fm, "cursor")
    manual_steps: list[str] = []

    # Adapt body content for Cursor
    adapted_body, body_warnings = adapt_body_content(body, "cursor")
    warnings.extend(body_warnings)

    skill_name = fm.get("name", skill_path.name)
    target_dir = output_dir / "cursor" / skill_name

    target_dir.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []

    # Generate SKILL.md with cleaned frontmatter and adapted body
    skill_md_content = generate_frontmatter_text(cleaned_fm) + "\n\n" + adapted_body
    (target_dir / "SKILL.md").write_text(skill_md_content)
    files_created.append(f"{skill_name}/SKILL.md")

    # Generate .cursor/rules/<name>.mdc rule file
    rules_dir = target_dir / "rules"
    rules_dir.mkdir(exist_ok=True)
    cursor_rule = generate_cursor_rule(fm, adapted_body)
    (rules_dir / f"{skill_name}.mdc").write_text(cursor_rule)
    files_created.append(f"{skill_name}/rules/{skill_name}.mdc")

    # Copy scripts if present
    src_scripts = skill_path / "scripts"
    if src_scripts.is_dir():
        dst_scripts = target_dir / "scripts"
        shutil.copytree(src_scripts, dst_scripts, dirs_exist_ok=True)
        for f in dst_scripts.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "cursor")))

    # Copy references if present
    src_refs = skill_path / "references"
    if src_refs.is_dir():
        dst_refs = target_dir / "references"
        shutil.copytree(src_refs, dst_refs, dirs_exist_ok=True)
        for f in dst_refs.rglob("*"):
            if f.is_file():
                files_created.append(str(f.relative_to(output_dir / "cursor")))

    tier = detect_skill_tier(skill_path)
    if tier >= 3:
        manual_steps.append("Routing table is Claude Code specific. Cursor uses description-based activation.")
    if tier >= 4:
        manual_steps.append("Cursor has single-level subagents only (Background Agents, Ultra plan). Task tool delegation needs manual adaptation.")

    classification = classify_frontmatter_fields(fm)

    return {
        "output_dir": str(target_dir),
        "files_created": files_created,
        "compatibility_score": calculate_compatibility_score(classification),
        "warnings": warnings,
        "manual_steps": manual_steps,
    }


# --- MCP Config Conversion ---

def convert_mcp_json_to_toml(mcp_json_path: Path) -> str | None:
    """Convert .mcp.json (Claude format) to TOML (Codex format).

    Returns TOML string or None if file not found.
    """
    if not mcp_json_path.exists():
        return None

    try:
        data = json.loads(mcp_json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    servers = data.get("mcpServers", {})
    if not servers:
        return None

    lines: list[str] = []
    for name, config in servers.items():
        lines.append(f"[mcp_servers.{name}]")

        command = config.get("command", "")
        if command:
            lines.append(f'command = "{command}"')

        server_type = config.get("type", "stdio")
        lines.append(f'type = "{server_type}"')

        args = config.get("args", [])
        if args:
            args_str = ", ".join(f'"{a}"' for a in args)
            lines.append(f"args = [{args_str}]")

        env = config.get("env", {})
        if env:
            lines.append(f"")
            lines.append(f"[mcp_servers.{name}.env]")
            for key, value in env.items():
                lines.append(f'{key} = "{value}"')

        lines.append("")

    return "\n".join(lines)


def convert_mcp_json_for_json_platform(mcp_json_path: Path, platform: str) -> str | None:
    """Convert .mcp.json to JSON format for Gemini, Antigravity, or Cursor.

    Gemini uses settings.json, Antigravity uses mcp_config.json,
    Cursor uses mcp.json. All use the same mcpServers JSON schema.
    """
    if not mcp_json_path.exists():
        return None

    try:
        data = json.loads(mcp_json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    servers = data.get("mcpServers", {})
    if not servers:
        return None

    output = {"mcpServers": servers}
    return json.dumps(output, indent=2)


# --- Multi-Platform Install Script ---

def generate_multiplatform_install(skill_name: str, platforms: list[str]) -> str:
    """Generate a multi-platform install.sh that detects the agent platform."""
    lines = [
        '#!/usr/bin/env bash',
        f'# Multi-platform installer for {skill_name}',
        f'# Supports: Claude Code, {", ".join(p.title() for p in platforms)}',
        '# Usage: bash install.sh [--platform claude|codex|gemini|antigravity|cursor]',
        '',
        'set -euo pipefail',
        '',
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'PLATFORM="${1:-auto}"',
        '',
        'detect_platform() {',
        '    if [ -d "$HOME/.claude" ]; then',
        '        echo "claude"',
    ]

    if "codex" in platforms:
        lines += [
            '    elif [ -d "$HOME/.agents" ]; then',
            '        echo "codex"',
        ]
    if "cursor" in platforms:
        lines += [
            '    elif [ -d "$HOME/.cursor" ]; then',
            '        echo "cursor"',
        ]
    if "gemini" in platforms or "antigravity" in platforms:
        lines += [
            '    elif [ -d "$HOME/.gemini" ]; then',
            '        echo "gemini"',
        ]

    lines += [
        '    else',
        '        echo "claude"  # Default',
        '    fi',
        '}',
        '',
        'if [ "$PLATFORM" = "auto" ] || [ "$PLATFORM" = "--auto" ]; then',
        '    PLATFORM=$(detect_platform)',
        '    echo "Detected platform: $PLATFORM"',
        'fi',
        '',
        '# Strip -- prefix if provided as flag',
        'PLATFORM="${PLATFORM#--}"',
        'PLATFORM="${PLATFORM#--platform=}"',
        '',
        'case "$PLATFORM" in',
        '    claude)',
        f'        SKILL_DIR="$HOME/.claude/skills"',
        '        ;;',
    ]

    if "codex" in platforms:
        lines += [
            '    codex)',
            f'        SKILL_DIR="$HOME/.agents/skills"',
            '        ;;',
        ]
    if "gemini" in platforms:
        lines += [
            '    gemini)',
            f'        SKILL_DIR="$HOME/.gemini/skills"',
            '        ;;',
        ]
    if "antigravity" in platforms:
        lines += [
            '    antigravity)',
            f'        SKILL_DIR="$HOME/.gemini/antigravity/skills"',
            '        ;;',
        ]
    if "cursor" in platforms:
        lines += [
            '    cursor)',
            f'        SKILL_DIR="$HOME/.cursor/skills"',
            '        ;;',
        ]

    lines += [
        '    *)',
        '        echo "Unknown platform: $PLATFORM"',
        '        echo "Supported: claude, ' + ", ".join(platforms) + '"',
        '        exit 1',
        '        ;;',
        'esac',
        '',
        'echo "Installing to: $SKILL_DIR"',
        'mkdir -p "$SKILL_DIR"',
        '',
        f'# Copy skill for the target platform',
        'if [ -d "$SCRIPT_DIR/$PLATFORM" ]; then',
        f'    cp -r "$SCRIPT_DIR/$PLATFORM"/* "$SKILL_DIR/"',
        'elif [ -d "$SCRIPT_DIR/claude" ]; then',
        '    # Fallback to claude version',
        f'    cp -r "$SCRIPT_DIR/claude"/* "$SKILL_DIR/"',
        'fi',
        '',
        'echo ""',
        f'echo "{skill_name} installed for $PLATFORM!"',
        '',
    ]

    return "\n".join(lines) + "\n"


# --- Main Conversion ---

def convert_skill(
    skill_path: str,
    targets: list[str],
    output_dir: str,
    dry_run: bool = False,
    include_mcp: bool = False,
) -> dict[str, Any]:
    """Convert a Claude Code skill to target platforms."""
    path = Path(skill_path).resolve()
    out = Path(output_dir).resolve()

    # Validate input
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return {"status": "error", "message": f"SKILL.md not found in {path}"}

    content = skill_md.read_text()
    fm, body, parse_errors = parse_frontmatter(content)
    if not fm:
        return {"status": "error", "message": f"Invalid frontmatter: {'; '.join(parse_errors)}"}

    skill_name = fm.get("name", path.name)
    tier = detect_skill_tier(path)
    classification = classify_frontmatter_fields(fm)

    # Dry run: just report compatibility
    if dry_run:
        platform_scores: dict[str, Any] = {}
        for target in targets:
            _, warnings = strip_claude_fields(fm, target)
            _, body_warnings = adapt_body_content(body, target)
            warnings.extend(body_warnings)
            manual_steps: list[str] = []
            if tier >= 3:
                manual_steps.append(f"Tier {tier} skill: routing and orchestration need manual adaptation for {target}.")
            if tier >= 4:
                manual_steps.append(f"Subagent delegation needs manual adaptation for {target}.")

            platform_scores[target] = {
                "compatibility_score": calculate_compatibility_score(classification),
                "warnings": warnings,
                "manual_steps": manual_steps,
                "fields_portable": classification["portable"],
                "fields_adaptable": classification["adaptable"],
                "fields_claude_only": classification["claude_only"],
            }

        return {
            "status": "dry_run",
            "skill_name": skill_name,
            "tier": tier,
            "platforms": platform_scores,
        }

    # Full conversion
    out.mkdir(parents=True, exist_ok=True)

    platform_results: dict[str, Any] = {}
    generators = {
        "codex": generate_codex_output,
        "gemini": generate_gemini_output,
        "antigravity": generate_antigravity_output,
        "cursor": generate_cursor_output,
    }

    for target in targets:
        if target in generators:
            platform_results[target] = generators[target](path, fm, body, out)

    # MCP config conversion
    if include_mcp:
        mcp_json = path / ".mcp.json"
        if not mcp_json.exists():
            mcp_json = path.parent / ".mcp.json"

        if mcp_json.exists():
            # Codex: convert to TOML
            if "codex" in targets:
                toml_content = convert_mcp_json_to_toml(mcp_json)
                if toml_content:
                    codex_dir = out / "codex" / skill_name
                    codex_dir.mkdir(parents=True, exist_ok=True)
                    (codex_dir / "config.toml").write_text(toml_content)
                    if "codex" in platform_results:
                        platform_results["codex"]["files_created"].append(f"{skill_name}/config.toml")

            # Gemini, Antigravity, Cursor: convert to platform-specific JSON
            json_platforms = {"gemini": "settings.json", "antigravity": "mcp_config.json", "cursor": "mcp.json"}
            for platform, filename in json_platforms.items():
                if platform in targets:
                    json_content = convert_mcp_json_for_json_platform(mcp_json, platform)
                    if json_content:
                        platform_dir = out / platform / skill_name
                        platform_dir.mkdir(parents=True, exist_ok=True)
                        (platform_dir / filename).write_text(json_content)
                        if platform in platform_results:
                            platform_results[platform]["files_created"].append(f"{skill_name}/{filename}")

    # Generate multi-platform install script
    install_script_path = out / "install-multiplatform.sh"
    install_content = generate_multiplatform_install(skill_name, targets)
    install_script_path.write_text(install_content)
    os.chmod(install_script_path, 0o755)

    return {
        "status": "success",
        "skill_name": skill_name,
        "tier": tier,
        "platforms": platform_results,
        "install_script": str(install_script_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Claude Code skills to other platforms"
    )
    parser.add_argument("path", help="Path to skill directory")
    parser.add_argument(
        "--target", "-t", default="all",
        help="Comma-separated targets: codex,gemini,antigravity,cursor,all (default: all)"
    )
    parser.add_argument(
        "--output", "-o", default="./dist",
        help="Output directory (default: ./dist)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Analyze compatibility without generating files"
    )
    parser.add_argument(
        "--include-mcp", action="store_true",
        help="Convert .mcp.json config files for target platforms"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(json.dumps({"status": "error", "message": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    targets = args.target.split(",")
    if "all" in targets:
        targets = ["codex", "gemini", "antigravity", "cursor"]

    valid_targets = {"codex", "gemini", "antigravity", "cursor"}
    invalid = set(targets) - valid_targets
    if invalid:
        print(json.dumps({"status": "error", "message": f"Invalid targets: {', '.join(invalid)}"}), file=sys.stderr)
        sys.exit(1)

    result = convert_skill(args.path, targets, args.output, args.dry_run, args.include_mcp)

    if result["status"] == "error":
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
