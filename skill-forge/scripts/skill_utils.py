#!/usr/bin/env python3
"""
Purpose: Shared utilities for skill-forge scripts.
Input: N/A (library module)
Output: N/A (library module)
Usage: from skill_utils import parse_frontmatter
"""

import re
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


def parse_frontmatter_simple(content: str) -> tuple[dict[str, Any] | None, str]:
    """Simplified parse_frontmatter that returns (frontmatter, body) without errors.

    Convenience wrapper for scripts that don't need error details.
    """
    frontmatter, body, _ = parse_frontmatter(content)
    return frontmatter, body
