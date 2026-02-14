#!/usr/bin/env python3
"""
Purpose: Scaffold a new Claude Code skill with the correct directory structure.
Input: Skill name (kebab-case), tier (1-4), output path
Output: Created directory tree with placeholder SKILL.md files
Usage: python scripts/init_skill.py <name> --tier <1-4> --path <output-path>

Examples:
    python scripts/init_skill.py my-skill --tier 1
    python scripts/init_skill.py devops-toolkit --tier 3 --path ./output
    python scripts/init_skill.py seo-analyzer --tier 4 --sub audit,page,technical
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def validate_name(name: str) -> tuple[bool, str]:
    """Validate skill name follows kebab-case convention."""
    if not name:
        return False, "Name cannot be empty"
    if len(name) > 64:
        return False, f"Name too long ({len(name)} chars, max 64)"
    if not re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$', name):
        return False, "Name must be kebab-case (lowercase letters, numbers, hyphens)"
    if name.startswith('-') or name.endswith('-'):
        return False, "Name cannot start or end with hyphen"
    if '--' in name:
        return False, "Name cannot contain consecutive hyphens"
    if 'claude' in name.lower() or 'anthropic' in name.lower():
        return False, "Name cannot contain 'claude' or 'anthropic' (reserved)"
    return True, "Valid"


def create_frontmatter(name: str, description: str = "") -> str:
    """Generate YAML frontmatter for a SKILL.md file."""
    desc = description or f"TODO: Describe what {name} does and when to use it."
    return f"""---
name: {name}
description: >
  {desc}
---"""


def create_main_skill(name: str, tier: int, sub_skills: list[str]) -> str:
    """Generate main SKILL.md content based on tier."""
    frontmatter = create_frontmatter(name)

    if tier == 1:
        return f"""{frontmatter}

# {name.replace('-', ' ').title()}

## Instructions

### Step 1: TODO
Describe the first step of your workflow.

### Step 2: TODO
Describe the next step.

## Examples

### Example 1: TODO
User says: "TODO: example trigger"
Actions: TODO
Result: TODO

## Troubleshooting

### Error: TODO
Cause: TODO
Solution: TODO
"""

    routing_table = "\n".join(
        f"| `/{name} {s}` | `skills/{name}-{s}/SKILL.md` | TODO |"
        for s in sub_skills
    ) if sub_skills else "| TODO | TODO | TODO |"

    sub_list = "\n".join(
        f"{i}. **{name}-{s}** -- TODO: description"
        for i, s in enumerate(sub_skills, 1)
    ) if sub_skills else "1. TODO: Add sub-skills"

    refs_section = ""
    if tier >= 2:
        refs_section = """
## Reference Files

Load on-demand as needed:
- `references/TODO.md` -- TODO: description
"""

    agents_section = ""
    if tier == 4:
        agents_section = """
## Subagents

For parallel analysis:
- TODO: Define agent roles
"""

    return f"""{frontmatter}

# {name.replace('-', ' ').title()}

TODO: 1-2 sentence overview.

## Quick Reference

| Command | Routes to | Purpose |
|---------|-----------|---------|
| `/{name}` | Interactive mode | TODO |
{routing_table}

## Orchestration Logic

When user invokes `/{name}`:
1. Detect context
2. Route to appropriate sub-skill
3. Collect results
4. Generate report
{refs_section}
## Sub-Skills

{sub_list}
{agents_section}"""


def create_sub_skill(parent: str, child: str) -> str:
    """Generate sub-skill SKILL.md content."""
    name = f"{parent}-{child}"
    return f"""{create_frontmatter(name)}

# {child.replace('-', ' ').title()}

## Process

### Step 1: TODO
Describe what this sub-skill does.

### Step 2: TODO
Next step.

## Output Format

TODO: Define expected output structure.
"""


def create_agent(parent: str, role: str) -> str:
    """Generate agent definition with proper YAML frontmatter."""
    name = f"{parent}-{role}"
    return f"""---
name: {name}
description: >
  TODO: What this agent analyzes in parallel workflows.
  <example>User says: "TODO: example trigger"</example>
  <example>User says: "TODO: example trigger"</example>
model: inherit
color: blue
tools:
  - Read
  - Grep
  - Glob
---

You are a {role.replace('-', ' ')} specialist.

## Your Role

TODO: What this agent does in parallel workflows.

## Process

1. TODO: Step 1
2. TODO: Step 2
3. Score each item on a 0-10 scale
4. Calculate category score (0-100)

## Output Format

Return results as structured markdown with findings table and recommendations.

## Cross-References

- Load `references/TODO.md` for domain knowledge
"""


def create_script_template(name: str) -> str:
    """Generate a placeholder Python script."""
    return f'''#!/usr/bin/env python3
"""
Purpose: TODO: What this script does
Input: TODO: Expected input format
Output: TODO: Expected output format
Usage: python scripts/{name}.py [args]
"""

import argparse
import json
import sys
from typing import Any


def main(args: argparse.Namespace) -> dict[str, Any]:
    """Main execution function."""
    # TODO: Implement
    return {{"status": "success", "data": {{}}}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TODO: Script description")
    parser.add_argument("input", help="TODO: Input description")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    try:
        result = main(args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({{"error": str(e)}}), file=sys.stderr)
        sys.exit(1)
'''


def scaffold(name: str, tier: int, output_path: str,
             sub_skills: list[str] | None = None) -> dict[str, Any]:
    """Create the full skill directory structure."""
    base = Path(output_path)
    created_files: list[str] = []

    # Default sub-skills for higher tiers
    if sub_skills is None and tier >= 3:
        sub_skills = ["sub1", "sub2", "sub3"]
    elif sub_skills is None:
        sub_skills = []

    # Main skill directory
    main_dir = base / name
    main_dir.mkdir(parents=True, exist_ok=True)

    # SKILL.md
    skill_md = main_dir / "SKILL.md"
    skill_md.write_text(create_main_skill(name, tier, sub_skills))
    created_files.append(str(skill_md))

    # References (tier 2+)
    if tier >= 2:
        refs_dir = main_dir / "references"
        refs_dir.mkdir(exist_ok=True)
        ref_file = refs_dir / "domain-knowledge.md"
        ref_file.write_text(f"# {name.replace('-', ' ').title()} Reference\n\nTODO: Add domain knowledge.\n")
        created_files.append(str(ref_file))

    # Scripts (tier 2+)
    if tier >= 2:
        scripts_dir = main_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        script = scripts_dir / "process.py"
        script.write_text(create_script_template("process"))
        script.chmod(0o755)
        created_files.append(str(script))

    # Sub-skills (tier 3+)
    if tier >= 3 and sub_skills:
        skills_dir = base / "skills"
        skills_dir.mkdir(exist_ok=True)
        for child in sub_skills:
            sub_dir = skills_dir / f"{name}-{child}"
            sub_dir.mkdir(exist_ok=True)
            sub_md = sub_dir / "SKILL.md"
            sub_md.write_text(create_sub_skill(name, child))
            created_files.append(str(sub_md))

    # Agents (tier 4)
    if tier == 4:
        agents_dir = base / "agents"
        agents_dir.mkdir(exist_ok=True)
        for child in sub_skills[:3]:  # Create agents for first 3 sub-skills
            agent_file = agents_dir / f"{name}-{child}.md"
            agent_file.write_text(create_agent(name, child))
            created_files.append(str(agent_file))

    # Assets (tier 3+)
    if tier >= 3:
        assets_dir = main_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

    return {
        "status": "success",
        "name": name,
        "tier": tier,
        "path": str(base),
        "files_created": len(created_files),
        "files": created_files,
    }


def main_cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scaffold a new Claude Code skill"
    )
    parser.add_argument("name", help="Skill name (kebab-case)")
    parser.add_argument(
        "--tier", type=int, choices=[1, 2, 3, 4], default=1,
        help="Complexity tier (1=minimal, 2=workflow, 3=multi-skill, 4=ecosystem)"
    )
    parser.add_argument(
        "--path", default=".",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--sub", default="",
        help="Comma-separated sub-skill names (e.g., audit,page,technical)"
    )
    args = parser.parse_args()

    # Validate name
    valid, msg = validate_name(args.name)
    if not valid:
        print(json.dumps({"error": f"Invalid skill name: {msg}"}), file=sys.stderr)
        sys.exit(1)

    # Check output path
    if not os.path.isdir(args.path):
        os.makedirs(args.path, exist_ok=True)

    # Check for existing skill
    if os.path.exists(os.path.join(args.path, args.name)):
        print(json.dumps({"error": f"Skill '{args.name}' already exists at {args.path}"}),
              file=sys.stderr)
        sys.exit(1)

    sub_skills = [s.strip() for s in args.sub.split(",") if s.strip()] if args.sub else None

    result = scaffold(args.name, args.tier, args.path, sub_skills)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main_cli()
