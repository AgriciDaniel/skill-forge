# Contributing to Skill Forge

Contributions are welcome. Here's how you can help.

## Bug Reports

Found a bug? Open an issue on [GitHub Issues](https://github.com/AgriciDaniel/skill-forge/issues) with:

1. What you expected to happen
2. What actually happened
3. Steps to reproduce
4. Your environment (OS, Python version, Claude Code version)

## Feature Suggestions

Have an idea? Start a conversation on [GitHub Discussions](https://github.com/AgriciDaniel/skill-forge/discussions) before opening a PR. This helps align on approach and prevents duplicate work.

## Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes
4. Validate your changes:
   ```bash
   python skill-forge/scripts/validate_skill.py skill-forge/
   ```
5. Commit with a clear message (`git commit -m "feat: add new feature"`)
6. Push to your fork (`git push origin feat/my-feature`)
7. Open a Pull Request against `main`

## Code Style

- **SKILL.md files**: Under 500 lines, valid YAML frontmatter, kebab-case naming
- **Python scripts**: Docstrings, type hints, argparse CLI, JSON output, stdlib only
- **Reference files**: Focused on one topic, under 200 lines, concrete examples
- **Agent definitions**: YAML frontmatter with name + description, body in second person
- **Naming**: kebab-case for directories and skill names, snake_case for Python files
- **Formatting**: Use em dash in titles and headings, not double dash

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code restructuring
- `test:` — Test additions or changes
