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
	@echo "  sync            Install all dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  format          Format code"
	@echo "  lint            Fix linting issues"
	@echo "  check           Type check"
	@echo ""
	@echo "Dependencies:"
	@echo "  add DEP=name              Add dependency"
	@echo "  add-opt GROUP=g DEP=name  Add optional"
	@echo "  add-dev DEP=name          Add dev dependency"
	@echo ""
	@echo "Version:"
	@echo "  version         Show version"
	@echo "  bump BUMP=patch|minor|major  Bump version"
	@echo ""
	@echo "Release:"
	@echo "  preflight       Pre-release checks"
	@echo "  build           Build package"
	@echo "  test-build      Test built package"
	@echo "  release         Tag release"
	@echo "  publish         Publish to PyPI"
	@echo "  full-release    Complete workflow"
	@echo "  clean           Clean build artifacts"

# Development
.PHONY: sync
sync:
	@echo "→ Syncing dependencies..."
	@uv sync
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

# Version Management
.PHONY: version
version:
	@VERSION=$$(grep '^version' pyproject.toml | cut -d'"' -f2); \
	echo "$(PACKAGE): $$VERSION"

.PHONY: bump
bump:
	@if [ -z "$(BUMP)" ]; then \
		echo "✗ Usage: make bump BUMP=patch|minor|major"; \
		exit 1; \
	fi
	@echo "→ Bumping $(PACKAGE) version ($(BUMP))..."
	@uv version --bump $(BUMP) --no-sync
	@VERSION=$$(grep '^version' pyproject.toml | cut -d'"' -f2); \
	echo "✓ Bumped to $$VERSION"

# Building & Testing
.PHONY: build
build:
	@echo "→ Building $(PACKAGE) package..."
	@uv build --no-sources --out-dir dist
	@echo "✓ Built in dist/"

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
	@echo -n "  Package exists: "; \
	[ -f pyproject.toml ] && echo "✓" || (echo "✗" && exit 1)
	@echo -n "  Build system: "; \
	grep -q '^\[build-system\]' pyproject.toml && echo "✓" || echo "✗"
	@echo -n "  Has README: "; \
	[ -f README.md ] && echo "✓" || echo "✗"
	@echo -n "  Version: "; \
	grep '^version' pyproject.toml | cut -d'"' -f2

# Release Management
.PHONY: release
release:
	@VERSION=$$(grep '^version' pyproject.toml | cut -d'"' -f2); \
	echo "→ Releasing $(PACKAGE) v$$VERSION..."; \
	git tag -a v$$VERSION -m "Release $(PACKAGE) v$$VERSION"; \
	uv pip install -e .; \
	echo "✓ Tagged v$$VERSION"; \
	echo "✓ Installed $(PACKAGE) locally"; \
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

# Full Release Workflow
.PHONY: full-release
full-release: preflight build test-build
	@echo ""
	@echo "✓ Package $(PACKAGE) ready for release!"
	@echo ""
	@echo "Complete the release:"
	@echo "  1. make release     # Create git tag"
	@echo "  2. make publish     # Publish to PyPI"
	@echo "  3. git push origin && git push origin --tags"

# Clean build artifacts
.PHONY: clean
clean:
	@rm -rf dist/ build/ *.egg-info src/*.egg-info
	@echo "✓ Cleaned build artifacts"