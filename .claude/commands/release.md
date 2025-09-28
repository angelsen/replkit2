---
description: Build, test, and release Python packages using relkit
argument-hint: [version-bump]
---

Execute a complete package release workflow using relkit.

**Your task: Release a package (or the entire project) using relkit's atomic workflow.**

## Step 1: Status Check

Review the output to ensure:
- Git is clean (no uncommitted changes)
- Changelog has entries
- Code quality checks pass

## Step 3: Update CHANGELOG

Ensure CHANGELOG.md has entries in the [Unreleased] section:
- Document what was Added, Changed, Fixed, or Removed
- Use clear, user-focused descriptions
- Follow Keep a Changelog format

## Step 4: Version Bump & Release

```bash
relkit bump <patch|minor|major>
```

This atomically:
- Updates version in pyproject.toml
- Moves [Unreleased] to new version in CHANGELOG
- Commits changes
- Creates tag (v1.0.0)
- Pushes to remote

## Step 5: Build & Test

```bash
# Build distribution files
relkit build
```

## Step 6: Publish

```bash
# Publish to PyPI (will prompt for confirmation)
relkit publish
```

Note: Private packages (with "Private :: Do Not Upload" classifier) are blocked from PyPI.

## Key Points

- **relkit enforces**: Clean git state before operations
- **relkit blocks**: Building if dist/ has old files
- **relkit requires**: CHANGELOG entries for releases
- **relkit protects**: Against accidental public releases

## Quick One-Liner

For a full release after changes are ready:
```bash
relkit bump patch && \
relkit build && \
relkit publish
```
