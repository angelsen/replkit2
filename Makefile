# ReplKit2 - Stateful REPL Framework
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Configuration
PACKAGE := replkit2

# Help
.PHONY: help
help:
	@echo "ReplKit2 Development"
	@echo ""
	@echo "Development:"
	@echo "  sync            Install all dependencies (including optional)"
	@echo ""
	@echo "Quality:"
	@echo "  format          Format code"
	@echo "  lint            Fix linting issues"
	@echo "  check           Type check"
	@echo "  quality         Run all quality checks"
	@echo ""
	@echo "Dependencies:"
	@echo "  add DEP=name              Add dependency"
	@echo "  remove DEP=name           Remove dependency"
	@echo "  add-opt GROUP=g DEP=name  Add optional"
	@echo "  add-dev DEP=name          Add dev dependency"
	@echo "  deps-tree                 Show dependency tree"
	@echo "  deps-outdated             Check for outdated packages"
	@echo ""
	@echo "Version:"
	@echo "  version         Show version"
	@echo "  bump BUMP=patch|minor|major  Bump version"
	@echo "  changes         Show commits since last tag"
	@echo ""
	@echo "Release:"
	@echo "  preflight       Pre-release checks"
	@echo "  build           Build package"
	@echo "  build-check     Validate build config"
	@echo "  test-build      Test built package"
	@echo "  release         Tag release"
	@echo "  publish         Publish to PyPI"
	@echo "  verify-pypi     Verify PyPI has latest version"
	@echo "  full-release    Complete workflow"
	@echo ""
	@echo "Utilities:"
	@echo "  clean           Clean build artifacts"
	@echo "  export-requirements  Export requirements.txt"

# Development
.PHONY: sync
sync:
	@echo "→ Syncing dependencies..."
	@uv sync --all-extras
	@echo "✓ Done"

# Quality
.PHONY: format
format:
	@echo "→ Formatting code..."
	@uv run ruff format .
	@echo "✓ Done"

.PHONY: lint
lint:
	@echo "→ Fixing lints..."
	@uv run ruff check . --fix
	@echo "✓ Done"

.PHONY: check
check:
	@echo "→ Type checking..."
	@basedpyright
	@echo "✓ Done"

# Quality pipeline
.PHONY: quality
quality: format lint check
	@echo "✓ All quality checks passed"

# Dependencies
.PHONY: add
add:
	@if [ -z "$(DEP)" ]; then \
		echo "✗ Usage: make add DEP=package"; \
		exit 1; \
	fi
	@echo "→ Adding $(DEP)..."
	@uv add $(DEP)
	@echo "✓ Done"

.PHONY: add-opt
add-opt:
	@if [ -z "$(GROUP)" ] || [ -z "$(DEP)" ]; then \
		echo "✗ Usage: make add-opt GROUP=mcp|cli|examples DEP=package"; \
		exit 1; \
	fi
	@echo "→ Adding $(DEP) to [$(GROUP)]..."
	@uv add --optional $(GROUP) $(DEP)
	@echo "✓ Done"

.PHONY: add-dev
add-dev:
	@if [ -z "$(DEP)" ]; then \
		echo "✗ Usage: make add-dev DEP=package"; \
		exit 1; \
	fi
	@echo "→ Adding $(DEP) to dev..."
	@uv add --dev $(DEP)
	@echo "✓ Done"

.PHONY: remove
remove:
	@if [ -z "$(DEP)" ]; then \
		echo "✗ Usage: make remove DEP=package"; \
		exit 1; \
	fi
	@echo "→ Removing $(DEP)..."
	@uv remove $(DEP)
	@echo "✓ Done"

# Version Management
.PHONY: version
version:
	@echo -n "$(PACKAGE): "
	@uv version --short

.PHONY: bump
bump:
	@if [ -z "$(BUMP)" ]; then \
		echo "✗ Usage: make bump BUMP=patch|minor|major"; \
		exit 1; \
	fi
	@echo "→ Bumping $(PACKAGE) version ($(BUMP))..."
	@OLD_VERSION=$$(uv version --short); \
	uv version --bump $(BUMP) --no-sync; \
	NEW_VERSION=$$(uv version --short); \
	echo "✓ Bumped from $$OLD_VERSION to $$NEW_VERSION"
	@uv lock --check || echo "⚠ Lock file needs update - run 'uv lock'"

# Show changes since last tag
.PHONY: changes
changes:
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~10"); \
	echo "→ Changes since $$LAST_TAG:"; \
	echo ""; \
	git log $$LAST_TAG..HEAD --oneline --pretty=format:"  %h %s" | head -20; \
	echo ""; \
	echo ""; \
	COMMIT_COUNT=$$(git rev-list $$LAST_TAG..HEAD --count 2>/dev/null || echo "0"); \
	echo "  ($$COMMIT_COUNT commits since $$LAST_TAG)"

# Building & Testing
.PHONY: build
build:
	@echo "→ Building $(PACKAGE) package..."
	@uv build --out-dir dist
	@echo "→ Build artifacts:"
	@ls -lh dist/*.whl dist/*.tar.gz 2>/dev/null | tail -2
	@echo "✓ Built in dist/"

.PHONY: build-check
build-check:
	@echo "→ Validating build configuration..."
	@[ -f pyproject.toml ] && grep -q "^\[build-system\]" pyproject.toml && echo "✓ Build configuration valid" || (echo "✗ Build configuration invalid" && exit 1)

.PHONY: test-build
test-build:
	@if [ ! -d "dist" ]; then \
		echo "✗ No build found. Run 'make build' first"; \
		exit 1; \
	fi
	@echo "→ Testing $(PACKAGE) build..."
	@WHEEL=$$(ls dist/*.whl 2>/dev/null | head -1); \
	if [ -z "$$WHEEL" ]; then \
		echo "✗ No wheel found"; \
		exit 1; \
	fi; \
	uv run --with $$WHEEL --no-project -- python -c \
		"import replkit2; print('✓ Import successful')"

# Pre-flight Checks
.PHONY: preflight
preflight:
	@echo "→ Pre-flight checks for $(PACKAGE)..."
	@echo -n "  Project structure: "; \
	[ -f pyproject.toml ] && [ -f README.md ] && echo "✓" || (echo "✗" && exit 1)
	@echo -n "  Lock file: "; \
	uv lock --check && echo "✓" || (echo "✗ needs update - run 'uv lock'" && exit 1)
	@echo -n "  Build config: "; \
	grep -q "^\[build-system\]" pyproject.toml && echo "✓" || echo "✗"
	@echo -n "  Version: "; \
	uv version --short

# Release Management
.PHONY: release
release:
	@VERSION=$$(uv version --short); \
	echo "→ Releasing $(PACKAGE) v$$VERSION..."; \
	git tag -a v$$VERSION -m "Release $(PACKAGE) v$$VERSION"; \
	echo "→ Installing locally with all extras..."; \
	uv sync --all-extras; \
	echo "✓ Tagged v$$VERSION"; \
	echo "✓ Installed $(PACKAGE)[all] locally"; \
	echo ""; \
	echo "Next steps:"; \
	echo "  git push origin v$$VERSION"

# Publishing
.PHONY: publish
publish:
	@if [ ! -d "dist" ]; then \
		echo "✗ No build found. Run 'make build' first"; \
		exit 1; \
	fi
	@echo "→ Publishing $(PACKAGE) to PyPI..."
	@uv publish --token "$$(pass pypi/uv-publish)"
	@echo "✓ Published to PyPI"

# Verify PyPI release
.PHONY: verify-pypi
verify-pypi:
	@echo "→ Verifying $(PACKAGE) on PyPI..."
	@LATEST=$$(curl -s https://pypi.org/rss/project/$(PACKAGE)/releases.xml | \
		grep -oP '(?<=<title>)[0-9]+\.[0-9]+\.[0-9]+' | head -1); \
	LOCAL=$$(uv version --short); \
	if [ "$$LATEST" = "$$LOCAL" ]; then \
		echo "✓ PyPI has v$$LATEST (matches local)"; \
	else \
		echo "⚠ PyPI: v$$LATEST, Local: v$$LOCAL"; \
		echo "  Package may still be propagating..."; \
	fi

# Full Release Workflow
.PHONY: full-release
full-release: preflight build test-build
	@echo ""
	@echo "✓ Package $(PACKAGE) ready for release!"
	@echo ""
	@echo "Complete the release:"
	@echo "  1. make release      # Create git tag"
	@echo "  2. make publish      # Publish to PyPI"
	@echo "  3. make verify-pypi  # Verify on PyPI"
	@echo "  4. git push origin && git push origin --tags"

# Dependency utilities
.PHONY: deps-tree
deps-tree:
	@echo "→ Dependency tree..."
	@uv tree --depth 3

.PHONY: deps-outdated
deps-outdated:
	@echo "→ Checking for outdated dependencies..."
	@uv tree --outdated || true

# Export requirements
.PHONY: export-requirements
export-requirements:
	@echo "→ Exporting requirements..."
	@uv export --format requirements.txt --output-file requirements.txt --all-extras
	@echo "✓ Exported to requirements.txt"

# Clean build artifacts
.PHONY: clean
clean:
	@rm -rf dist/ build/ *.egg-info src/*.egg-info
	@echo "✓ Cleaned build artifacts"