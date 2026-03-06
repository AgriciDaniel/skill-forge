#!/usr/bin/env python3
"""
Purpose: Generate a starter eval set for a Claude Code skill based on its SKILL.md.
Input: Path to a skill directory containing SKILL.md
Output: JSON eval set with should-trigger and should-not-trigger queries
Usage: python scripts/generate_eval_set.py /path/to/skill [--output evals.json]

Analyzes the skill's description and instructions to produce:
- 10 should-trigger queries (various phrasings, edge cases)
- 10 should-not-trigger queries (near-misses, adjacent domains)
- Basic assertions for functional testing
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Use shared parser when available; inline fallback for standalone execution
try:
    from skill_utils import parse_frontmatter_simple as parse_frontmatter
except ImportError:
    def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:  # type: ignore[misc]
        """Parse YAML frontmatter from SKILL.md content (inline fallback)."""
        if not content.startswith('---'):
            return None, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content
        yaml_text, body = parts[1].strip(), parts[2].strip()
        frontmatter: dict[str, Any] = {}
        current_key, current_value, in_multiline = "", "", False
        for line in yaml_text.split('\n'):
            stripped = line.strip()
            if in_multiline:
                if stripped and not re.match(r'^[a-z_-]+:', stripped):
                    current_value += " " + stripped
                    continue
                frontmatter[current_key] = current_value.strip()
                in_multiline = False
            match = re.match(r'^([a-z_-]+):\s*(.*)', stripped)
            if match:
                current_key, value = match.group(1), match.group(2).strip()
                if value in ('>', '|'):
                    in_multiline, current_value = True, ""
                elif value:
                    frontmatter[current_key] = value.strip('"').strip("'")
        if in_multiline:
            frontmatter[current_key] = current_value.strip()
        return frontmatter, body


def extract_trigger_phrases(description: str) -> list[str]:
    """Extract quoted trigger phrases from the description."""
    phrases = re.findall(r'"([^"]+)"', description)
    return phrases


def extract_keywords(description: str) -> list[str]:
    """Extract domain keywords from the description."""
    stop_words = {
        'use', 'when', 'user', 'says', 'the', 'and', 'for', 'with', 'that',
        'this', 'from', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'does',
        'not', 'but', 'also', 'more', 'into', 'than', 'then', 'its', 'all',
        'any', 'each', 'both', 'such', 'only', 'own', 'same', 'other',
    }

    words = re.findall(r'[a-z]+(?:-[a-z]+)*', description.lower())
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:20]


def extract_headings(body: str) -> list[str]:
    """Extract section headings from the SKILL.md body."""
    headings = re.findall(r'^#{1,3}\s+(.+)$', body, re.MULTILINE)
    return headings


def generate_trigger_evals(
    name: str,
    description: str,
    trigger_phrases: list[str],
    keywords: list[str],
) -> list[dict[str, Any]]:
    """Generate should-trigger eval entries."""
    evals: list[dict[str, Any]] = []
    eval_id = 0

    # Direct trigger phrases from description
    for phrase in trigger_phrases[:5]:
        evals.append({
            "eval_id": eval_id,
            "eval_name": f"trigger-direct-{eval_id}",
            "prompt": f"I need to {phrase}",
            "input_files": [],
            "assertions": [
                {
                    "name": "skill-activated",
                    "check": f"The {name} skill activated and began its workflow",
                    "weight": 1.0,
                }
            ],
            "should_trigger": True,
        })
        eval_id += 1

    # Casual paraphrases
    casual_templates = [
        "hey can you help me {keyword} something?",
        "I've got this {keyword} task I need done",
        "so my boss wants me to {keyword} — can you handle that?",
        "quick question: how do I {keyword} with this tool?",
        "need to {keyword} asap, what's the best approach?",
    ]
    for i, template in enumerate(casual_templates):
        if i < len(keywords):
            evals.append({
                "eval_id": eval_id,
                "eval_name": f"trigger-casual-{eval_id}",
                "prompt": template.format(keyword=keywords[i]),
                "input_files": [],
                "assertions": [
                    {
                        "name": "skill-activated",
                        "check": f"The {name} skill activated and began its workflow",
                        "weight": 1.0,
                    }
                ],
                "should_trigger": True,
            })
            eval_id += 1

    return evals[:10]


def generate_negative_evals(
    name: str,
    keywords: list[str],
) -> list[dict[str, Any]]:
    """Generate should-not-trigger eval entries.

    Best practice: negative evals should be near-misses that share keywords
    with the skill but need different tools. Avoid obviously irrelevant
    queries like "what's the weather" — those don't test real disambiguation.
    """
    # Near-miss templates that share domain keywords but need different tools
    near_miss_templates = [
        "Can you explain what {keyword} means in general terms?",
        "Write documentation about the concept of {keyword} for my README",
        "I'm learning about {keyword} -- what are some good tutorials?",
        "What's the difference between {keyword} and similar approaches?",
        "Search GitHub for open-source projects related to {keyword}",
        "Debug this error I'm getting -- it mentions {keyword} in the stack trace",
        "Refactor this function that handles {keyword} logic to be more readable",
        "Add unit tests for the {keyword} module in my project",
        "Review this PR that changes how we handle {keyword}",
        "Set up a CI/CD pipeline that includes {keyword} validation steps",
    ]

    evals: list[dict[str, Any]] = []
    for i, template in enumerate(near_miss_templates[:10]):
        keyword = keywords[i % len(keywords)] if keywords else "this"
        evals.append({
            "eval_id": 100 + i,
            "eval_name": f"no-trigger-near-miss-{i}",
            "prompt": template.format(keyword=keyword),
            "input_files": [],
            "assertions": [
                {
                    "name": "skill-not-activated",
                    "check": f"The {name} skill did NOT activate",
                    "weight": 1.0,
                }
            ],
            "should_trigger": False,
        })

    return evals


def generate_eval_set(skill_path: str, output_path: str | None = None) -> dict[str, Any]:
    """Generate a complete eval set for a skill."""
    path = Path(skill_path).resolve()
    skill_md = path / "SKILL.md"

    if not skill_md.exists():
        return {"error": f"SKILL.md not found at {path}"}

    content = skill_md.read_text()
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        return {"error": "Could not parse SKILL.md frontmatter"}

    name = frontmatter.get("name", path.name)
    description = frontmatter.get("description", "")

    trigger_phrases = extract_trigger_phrases(description)
    keywords = extract_keywords(description)
    headings = extract_headings(body)

    trigger_evals = generate_trigger_evals(name, description, trigger_phrases, keywords)
    negative_evals = generate_negative_evals(name, keywords)

    eval_set = {
        "skill_name": name,
        "skill_path": str(path),
        "generated_from": "description + instructions",
        "evals": trigger_evals + negative_evals,
        "metadata": {
            "trigger_phrases_found": len(trigger_phrases),
            "keywords_found": len(keywords),
            "headings_found": len(headings),
            "total_evals": len(trigger_evals) + len(negative_evals),
            "should_trigger_count": len(trigger_evals),
            "should_not_trigger_count": len(negative_evals),
        },
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(eval_set, indent=2))

    return eval_set


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a starter eval set for a Claude Code skill"
    )
    parser.add_argument("path", help="Path to skill directory containing SKILL.md")
    parser.add_argument(
        "--output", "-o",
        help="Output file path for eval set JSON (default: stdout)"
    )
    args = parser.parse_args()

    if not Path(args.path).is_dir():
        print(json.dumps({"error": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    result = generate_eval_set(args.path, args.output)

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    if not args.output:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            "status": "success",
            "output": args.output,
            "total_evals": result["metadata"]["total_evals"],
        }, indent=2))
