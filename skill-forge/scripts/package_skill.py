#!/usr/bin/env python3
"""
Purpose: Package a Claude Code skill into a distributable .skill (ZIP) file.
Input: Path to skill directory (or parent with skills/ and agents/)
Output: .skill ZIP file ready for distribution
Usage: python scripts/package_skill.py /path/to/skill-root --output ./dist

The script packages:
- Main skill directory (skill-name/)
- Sub-skill directories (skills/skill-name-*/)
- Agent definitions (agents/skill-name-*.md)
- Scripts directory (scripts/)
- install.sh (if present)
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any


EXCLUDED_PATTERNS = {
    '__pycache__',
    '.pyc',
    '.pyo',
    '.egg-info',
    '.git',
    '.tmp',
    '.env',
    'node_modules',
    '.DS_Store',
    'Thumbs.db',
}


def should_exclude(path: Path) -> bool:
    """Check if a file/directory should be excluded from the package."""
    for part in path.parts:
        for pattern in EXCLUDED_PATTERNS:
            if part == pattern or part.endswith(pattern):
                return True
    return False


def find_skill_name(skill_path: Path) -> str | None:
    """Extract skill name from SKILL.md frontmatter."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text()
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('name:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")
    return None


def collect_files(root: Path, skill_name: str) -> list[tuple[Path, str]]:
    """Collect all files to include in the package.

    Returns list of (absolute_path, archive_path) tuples.
    """
    files: list[tuple[Path, str]] = []

    # Main skill directory
    main_dir = root / skill_name
    if main_dir.is_dir():
        for f in main_dir.rglob('*'):
            if f.is_file() and not should_exclude(f):
                archive_path = str(f.relative_to(root))
                files.append((f, archive_path))

    # Sub-skills directory
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for sub_dir in skills_dir.iterdir():
            if sub_dir.is_dir() and sub_dir.name.startswith(f"{skill_name}-"):
                for f in sub_dir.rglob('*'):
                    if f.is_file() and not should_exclude(f):
                        archive_path = str(f.relative_to(root))
                        files.append((f, archive_path))

    # Agents directory
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.glob(f"{skill_name}-*.md"):
            if f.is_file():
                archive_path = str(f.relative_to(root))
                files.append((f, archive_path))

    # Scripts directory
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        for f in scripts_dir.rglob('*'):
            if f.is_file() and not should_exclude(f):
                archive_path = str(f.relative_to(root))
                files.append((f, archive_path))

    # Install script
    install_sh = root / "install.sh"
    if install_sh.exists():
        files.append((install_sh, "install.sh"))

    # LICENSE
    for license_name in ["LICENSE", "LICENSE.txt", "LICENSE.md"]:
        license_file = root / license_name
        if license_file.exists():
            files.append((license_file, license_name))
            break

    return files


def package_skill(root_path: str, output_dir: str) -> dict[str, Any]:
    """Package a skill into a .skill ZIP file."""
    root = Path(root_path).resolve()
    out = Path(output_dir).resolve()

    # Find the main skill directory
    skill_name = None
    for item in root.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skill_name = find_skill_name(item)
            if skill_name:
                break

    if not skill_name:
        return {"error": "No valid skill found (no SKILL.md with name field)"}

    # Collect files
    files = collect_files(root, skill_name)
    if not files:
        return {"error": "No files found to package"}

    # Create output directory
    out.mkdir(parents=True, exist_ok=True)

    # Create ZIP
    zip_path = out / f"{skill_name}.skill"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arc_path in files:
            zf.write(abs_path, arc_path)

    return {
        "status": "success",
        "skill_name": skill_name,
        "package": str(zip_path),
        "files_included": len(files),
        "size_bytes": zip_path.stat().st_size,
        "files": [arc for _, arc in files],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Package a Claude Code skill for distribution"
    )
    parser.add_argument("path", help="Path to skill root directory")
    parser.add_argument(
        "--output", "-o", default="./dist",
        help="Output directory for .skill file (default: ./dist)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(json.dumps({"error": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    result = package_skill(args.path, args.output)

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
