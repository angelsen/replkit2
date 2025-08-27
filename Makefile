# ReplKit2 - Minimal development helpers
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "ReplKit2 Development"
	@echo ""
	@echo "  make sync    Install all dependencies"
	@echo ""
	@echo "For releases, use relkit:"
	@echo "  relkit status   - Check release readiness"
	@echo "  relkit check    - Run quality checks"
	@echo "  relkit bump     - Version and release"
	@echo "  relkit build    - Build package"
	@echo "  relkit publish  - Publish to PyPI"

.PHONY: sync
sync:
	@echo "→ Syncing all dependencies..."
	@uv sync --all-packages --all-extras --all-groups
	@echo "✓ Done"