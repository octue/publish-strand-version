# Claude Code Instructions

## Version bumps

When bumping the version, review README.md and other documentation/examples for hardcoded version references (e.g. in `uses:` lines or Docker image tags) and update them to match the new version.

## GitHub workflows

When editing GitHub workflow files (`.github/workflows/*.yml`), always lint against the GitHub Workflows YAML schema to catch syntax errors before committing.
