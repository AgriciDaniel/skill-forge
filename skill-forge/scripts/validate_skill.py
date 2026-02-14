#!/usr/bin/env python3
"""
Purpose: Validate a Claude Code skill's structure, frontmatter, and quality.
Input: Path to a skill directory
Output: JSON validation report with pass/fail status and issues
Usage: python scripts/validate_skill.py /path/to/skill [--strict]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


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

    # Basic YAML parsing (handles simple key: value and multiline >)
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
                # Check if next line starts a list
                in_list = True
                current_list = []
            else:
                frontmatter[current_key] = value.strip('"').strip("'")

    # Handle final multiline/list value
    if in_multiline:
        frontmatter[current_key] = current_value.strip()
    if in_list and current_list:
        frontmatter[current_key] = current_list

    return frontmatter, body, errors


def validate_name(name: str, folder_name: str) -> list[str]:
    """Validate the 'name' field."""
    issues: list[str] = []

    if not name:
        issues.append("CRITICAL: 'name' field is missing")
        return issues

    if len(name) > 64:
        issues.append(f"CRITICAL: Name too long ({len(name)} chars, max 64)")

    if not re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$', name):
        issues.append(f"CRITICAL: Name '{name}' is not valid kebab-case")

    if name.startswith('-') or name.endswith('-'):
        issues.append("CRITICAL: Name cannot start or end with hyphen")

    if '--' in name:
        issues.append("CRITICAL: Name cannot contain consecutive hyphens")

    if 'claude' in name.lower() or 'anthropic' in name.lower():
        issues.append("CRITICAL: Name cannot contain 'claude' or 'anthropic'")

    if name != folder_name:
        issues.append(f"HIGH: Name '{name}' does not match folder name '{folder_name}'")

    return issues


def validate_description(description: str) -> list[str]:
    """Validate the 'description' field."""
    issues: list[str] = []

    if not description:
        issues.append("CRITICAL: 'description' field is missing")
        return issues

    if len(description) > 1024:
        issues.append(f"CRITICAL: Description too long ({len(description)} chars, max 1024)")

    if '<' in description or '>' in description:
        issues.append("CRITICAL: Description contains XML angle brackets (< >)")

    # Check for WHAT component
    has_what = len(description) > 20
    if not has_what:
        issues.append("HIGH: Description too short to explain capabilities")

    # Check for WHEN component (trigger phrases)
    trigger_patterns = [
        r'[Uu]se when',
        r'[Tt]rigger',
        r'[Uu]ser says',
        r'[Uu]se for',
        r'[Ww]hen .* says',
    ]
    has_when = any(re.search(p, description) for p in trigger_patterns)
    if not has_when:
        issues.append("HIGH: Description missing trigger phrases (add 'Use when user says...')")

    # Check for keywords
    if description.count('"') < 2:
        issues.append("MEDIUM: Description has few quoted trigger phrases (recommend 5-10)")

    return issues


def validate_structure(skill_path: Path) -> list[str]:
    """Validate directory structure."""
    issues: list[str] = []

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        # Check for case variations
        for f in skill_path.iterdir():
            if f.name.lower() == "skill.md" and f.name != "SKILL.md":
                issues.append(f"CRITICAL: Found '{f.name}' but must be exactly 'SKILL.md'")
                break
        else:
            issues.append("CRITICAL: SKILL.md not found")
        return issues

    # Check for README.md inside skill folder
    if (skill_path / "README.md").exists():
        issues.append("MEDIUM: README.md found inside skill folder (should be repo-level only)")

    # Check folder name
    folder_name = skill_path.name
    if not re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$', folder_name):
        issues.append(f"HIGH: Folder name '{folder_name}' is not valid kebab-case")

    return issues


def validate_body(body: str) -> list[str]:
    """Validate SKILL.md body content."""
    issues: list[str] = []

    lines = body.split('\n')
    line_count = len(lines)

    if line_count > 500:
        issues.append(f"MEDIUM: SKILL.md body is {line_count} lines (recommend <500)")

    if line_count < 10:
        issues.append("MEDIUM: SKILL.md body seems too short (<10 lines)")

    # Estimate token count (rough: ~4 chars per token)
    char_count = len(body)
    est_tokens = char_count // 4
    if est_tokens > 5000:
        issues.append(f"MEDIUM: Estimated ~{est_tokens} tokens (recommend <5000)")

    # Check for headings
    headings = [l for l in lines if l.startswith('#')]
    if len(headings) < 2:
        issues.append("LOW: Few headings found (use ## sections for organization)")

    return issues


def validate_scripts(skill_path: Path) -> list[str]:
    """Validate scripts if present."""
    issues: list[str] = []
    scripts_dir = skill_path / "scripts"

    if not scripts_dir.exists():
        return issues

    for script in scripts_dir.glob("*.py"):
        content = script.read_text()

        if '"""' not in content and "'''" not in content:
            issues.append(f"LOW: Script {script.name} missing docstring")

        if 'argparse' not in content and 'sys.argv' not in content:
            issues.append(f"LOW: Script {script.name} has no CLI interface")

    return issues


def validate_agent(agent_path: Path) -> list[str]:
    """Validate an agent definition file."""
    issues: list[str] = []

    if not agent_path.exists():
        issues.append(f"CRITICAL: Agent file not found: {agent_path}")
        return issues

    content = agent_path.read_text()

    # Check for YAML frontmatter
    if not content.startswith('---'):
        issues.append("CRITICAL: Agent missing YAML frontmatter (must start with ---)")
        return issues

    parts = content.split('---', 2)
    if len(parts) < 3:
        issues.append("CRITICAL: Agent missing closing '---' delimiter")
        return issues

    yaml_text = parts[1].strip()
    body = parts[2].strip()

    # Check required fields
    has_name = False
    has_description = False
    agent_name = ""

    for line in yaml_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('name:'):
            has_name = True
            agent_name = stripped.split(':', 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith('description:'):
            has_description = True

    if not has_name:
        issues.append("CRITICAL: Agent missing 'name' field")
    elif agent_name:
        if len(agent_name) < 3 or len(agent_name) > 50:
            issues.append(f"HIGH: Agent name '{agent_name}' should be 3-50 chars (got {len(agent_name)})")
        expected_name = agent_path.stem  # filename without .md
        if agent_name != expected_name:
            issues.append(f"HIGH: Agent name '{agent_name}' doesn't match filename '{expected_name}'")

    if not has_description:
        issues.append("CRITICAL: Agent missing 'description' field")

    # Check body (system prompt)
    if len(body) < 20:
        issues.append("HIGH: Agent body (system prompt) too short")

    return issues


def calculate_score(issues: list[str]) -> int:
    """Calculate health score based on issues found."""
    score = 100

    for issue in issues:
        if issue.startswith("CRITICAL:"):
            score -= 20
        elif issue.startswith("HIGH:"):
            score -= 10
        elif issue.startswith("MEDIUM:"):
            score -= 5
        elif issue.startswith("LOW:"):
            score -= 2

    return max(0, score)


def validate_skill(skill_path: str, strict: bool = False) -> dict[str, Any]:
    """Run full validation on a skill directory."""
    path = Path(skill_path).resolve()
    all_issues: list[str] = []

    # Structure validation
    all_issues.extend(validate_structure(path))

    # If SKILL.md doesn't exist, we can't do more
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return {
            "status": "fail",
            "path": str(path),
            "score": 0,
            "issues": all_issues,
        }

    content = skill_md.read_text()

    # Parse frontmatter
    frontmatter, body, parse_errors = parse_frontmatter(content)
    all_issues.extend(parse_errors)

    if frontmatter:
        # Name validation
        name = frontmatter.get("name", "")
        all_issues.extend(validate_name(name, path.name))

        # Description validation
        description = frontmatter.get("description", "")
        all_issues.extend(validate_description(description))

        # Check optional fields
        if "compatibility" in frontmatter:
            compat = frontmatter["compatibility"]
            if isinstance(compat, str) and len(compat) > 500:
                all_issues.append(
                    f"MEDIUM: Compatibility too long ({len(compat)} chars, max 500)"
                )

    # Body validation
    all_issues.extend(validate_body(body))

    # Script validation
    all_issues.extend(validate_scripts(path))

    # Calculate score
    score = calculate_score(all_issues)
    status = "pass" if score >= 60 else "fail"
    if strict and score < 80:
        status = "fail"

    return {
        "status": status,
        "path": str(path),
        "name": frontmatter.get("name", "unknown") if frontmatter else "unknown",
        "score": score,
        "issues_count": len(all_issues),
        "critical": [i for i in all_issues if i.startswith("CRITICAL:")],
        "high": [i for i in all_issues if i.startswith("HIGH:")],
        "medium": [i for i in all_issues if i.startswith("MEDIUM:")],
        "low": [i for i in all_issues if i.startswith("LOW:")],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate a Claude Code skill or agent"
    )
    parser.add_argument("path", help="Path to skill directory or agent file")
    parser.add_argument(
        "--strict", action="store_true",
        help="Strict mode: require score >= 80"
    )
    parser.add_argument(
        "--agent", action="store_true",
        help="Validate an agent .md file instead of a skill directory"
    )
    args = parser.parse_args()

    if args.agent:
        # Validate agent file
        agent_path = Path(args.path).resolve()
        if not agent_path.exists():
            print(json.dumps({"error": f"File not found: {args.path}"}), file=sys.stderr)
            sys.exit(1)
        issues = validate_agent(agent_path)
        score = calculate_score(issues)
        result = {
            "status": "pass" if score >= 60 else "fail",
            "path": str(agent_path),
            "type": "agent",
            "score": score,
            "issues_count": len(issues),
            "critical": [i for i in issues if i.startswith("CRITICAL:")],
            "high": [i for i in issues if i.startswith("HIGH:")],
            "medium": [i for i in issues if i.startswith("MEDIUM:")],
            "low": [i for i in issues if i.startswith("LOW:")],
        }
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "pass" else 1)

    if not os.path.isdir(args.path):
        print(json.dumps({"error": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    result = validate_skill(args.path, args.strict)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["status"] == "pass" else 1)
