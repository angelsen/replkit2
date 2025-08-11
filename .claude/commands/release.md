---
description: Build, test, and publish ReplKit2 with proper versioning and PyPI deployment
argument-hint: [version-bump]
allowed-tools: Bash, Read, Edit, MultiEdit, Grep, Glob, Task
---

Build, test, and release ReplKit2 package to PyPI.

**Your task: Execute a complete package release workflow.**

## Phase 1: Pre-flight Checks

**Run comprehensive validation:**
```bash
make preflight        # Validates project, lock file, environment, build
make quality          # Runs format, lint, check, and all validations
```

**Additional checks:**
- Ensure CHANGELOG.md is up to date for the version
- Review dependency tree: `make deps-tree`
- Check for outdated packages: `make deps-outdated`

## Phase 2: Version Management

**Review changes since last release:**
```bash
make changes            # Show commits since last tag
```

**If version bump requested (patch/minor/major):**
```bash
make bump BUMP=<type>   # Bump version
uv lock                 # Update lock file after version change
make sync               # Ensure environment is synchronized
```

**Update CHANGELOG.md:**
- Use `make changes` output to identify what needs documenting
- Add new version section with today's date
- Group changes by category: Added, Changed, Fixed, Removed
- Follow Keep a Changelog format

## Phase 3: Build & Test

**Execute build pipeline:**
```bash
make clean              # Clean old artifacts
make build-check        # Validate build configuration
make build              # Build package
make test-build         # Test imports work
```

**Verify build artifacts:**
- Check `dist/` contains wheel and sdist
- Build output shows file sizes
- Version matches: `make version`

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
make verify-pypi        # Check RSS feed for latest version (immediate)
# Note: RSS feed updates immediately, JSON API has CDN delay
```

## Phase 6: Push to GitHub

```bash
git push origin main
git push origin v<version>
```

## Phase 7: Post-Release Verification

**Verify package appears on PyPI:**
```bash
make verify-pypi        # Confirm version matches local
```

**Test installation from PyPI (after propagation):**
```bash
# Test in isolated environment (downloads from PyPI if available):
uv run --isolated --with replkit2==<version> \
  python -c "from replkit2 import App; print('✓ Import successful')"
```

**Create GitHub release:**
- Use the new tag
- Copy relevant CHANGELOG section
- Highlight major features

## Key Strategies

- **Native uv commands**: No `uv pip`, use `uv sync`, `uv add`, etc.
- **Automatic lock management**: uv handles lock file in normal operations
- **Package-local builds**: dist/ directory in project root
- **PyPI compatibility first**: Fix any issues before building
- **Atomic releases**: Complete each phase before moving to next
- **Version consistency**: Use `uv version --short` for all version checks

Start by running `make preflight` to validate the project state.