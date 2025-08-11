---
description: Build, test, and publish ReplKit2 with proper versioning and PyPI deployment
argument-hint: [version-bump]
allowed-tools: Bash, Read, Edit, MultiEdit, Grep, Glob, Task
---

Build, test, and release ReplKit2 package to PyPI.

**Your task: Execute a complete package release workflow.**

## Phase 1: Pre-flight Checks

**Run Makefile preflight:**
```bash
make preflight
```
This checks:
- Package exists
- Build system configured
- README exists
- Current version

**Additional checks:**
- Ensure CHANGELOG.md is up to date for the version
- Run quality checks: `make format lint check`

## Phase 2: Version Management

**If version bump requested (patch/minor/major):**
```bash
make bump BUMP=<type>
```

**Update CHANGELOG.md:**
- Add new version section with today's date
- Document changes since last release
- Follow Keep a Changelog format

## Phase 3: Build & Test

**Execute build pipeline:**
```bash
make clean              # Clean old artifacts
make build              # Build with --no-sources
make test-build         # Test imports work
```

**Verify build artifacts:**
- Check `dist/` contains wheel and sdist
- Ensure version numbers match pyproject.toml

## Phase 4: Git Operations

**Commit any pending changes:**
```bash
git add -A
git commit -m "chore: prepare v<version> for release

- Update version to <version>
- Update CHANGELOG
- <any other changes>"
```

**Create release tag:**
```bash
make release  # Creates git tag, installs locally
```

## Phase 5: Distribution

**Publish to PyPI:**
```bash
make publish  # Publishes using uv publish
```

**Verify PyPI publication:**
```bash
# Check version on PyPI
curl -s https://pypi.org/pypi/replkit2/json | jq -r '.info.version'

# Check with uv
uv pip install --dry-run replkit2==<version>
```

## Phase 6: Push to GitHub

```bash
git push origin main
git push origin v<version>
```

## Phase 7: Post-Release Verification

**Verify package appears on PyPI:**
- Check installation: `uv add replkit2==<version>`
- Test with extras: `uv add "replkit2[all]==<version>"`

**Create GitHub release:**
- Use the new tag
- Copy relevant CHANGELOG section
- Highlight major features

## Key Strategies

- **Package-local builds**: dist/ directory in project root
- **PyPI compatibility first**: Fix any issues before building
- **Atomic releases**: Complete each phase before moving to next
- **Version consistency**: pyproject.toml drives all versioning

Start by checking if the package exists and confirming the version to release.