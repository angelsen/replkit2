# ReplKit2 Roadmap

## Overview

This document outlines potential future features and enhancements for ReplKit2. Items are not commitments but rather ideas under consideration. Community feedback is welcome via GitHub issues.

## Current Release - ExecutionContext ✅

### Completed in v0.13.0
Context-aware commands with mode detection and decorator parameter deprecation warnings.

**ExecutionContext features:**
- Commands can detect execution mode (REPL, MCP, CLI, programmatic)
- Opt-in via `_ctx: ExecutionContext = None` parameter
- Mode detection: `_ctx.is_repl()`, `_ctx.is_mcp()`, `_ctx.is_cli()`, `_ctx.is_programmatic()`
- Factory methods: `ExecutionContext.for_repl()`, `for_mcp()`, `for_cli()`, `for_programmatic()`, `for_test()`
- 100% backward compatible - commands without `_ctx` work unchanged

**Decorator-level parameter deprecation:**
- Decorator-level `truncate=` and `transforms=` parameters now deprecated
- FutureWarning issued at registration for affected commands
- Migration path: Use element-level `truncate`/`transforms` with `_ctx` for mode-aware formatting
- Note: `mime_type` is NOT deprecated - it's valid and recommended with `_ctx`

**Internal improvements:**
- Added `ExecutionContext.for_test()` factory method
- Replaced manual cache with `@lru_cache(maxsize=256)`
- Extracted MCP context creation helper
- Fixed 2 pre-existing bugs in resources.py

**Benefits:**
- Commands adapt behavior for different execution contexts
- Better UX: compact output for REPL, full data for MCP/CLI
- Explicit control over mode-specific formatting with `_ctx`
- Testable with explicit context passing

## Previous Release - Integration Architecture ✅

### Completed in v0.12.0
Multi-mode deployment with integration properties and programmatic access.

**Integration properties:**
- `app.mcp` - FastMCP server for LLM tools/resources/prompts
- `app.cli` - Typer CLI for traditional command-line interface
- `app.state` - Direct state access for API integrations
- `app.execute()` - Programmatic command execution

**Breaking changes:**
- Removed `using()` method
- Formatters now internal (TextFormatter only)
- Simplified API surface for clarity

**Benefits:**
- Write once, deploy as REPL/CLI/MCP/API
- Clear, explicit patterns for each mode
- Foundation for framework integrations
- No magic - users control their deployment

## MCP Tool Aliases ✅

### Completed in v0.7.3
Semantic aliases for MCP tools with parameter remapping support.

## Future Enhancement - FastAPI Helpers

### Goal
Provide optional convenience helpers for FastAPI integration (not automatic routing).

### Current State ✅
FastAPI integration works via `app.execute()` and `app.state`. Users have full control over routing and responses. See [`examples/todo_api.py`](examples/todo_api.py) and [`docs/integrations.md`](docs/integrations.md).

### Potential Helpers
```python
# Optional convenience wrapper (future)
from replkit2.integrations.fastapi import create_router

router = create_router(app, prefix="/api/todo")
fastapi_app.include_router(router)
```

### Considerations
- Should be optional (separate module/extra)
- Don't hide the web framework from users
- Focus on reducing boilerplate, not magic
- Support other frameworks (Flask, Django)?
- Community feedback needed on desired patterns

## Future Release - Plugin System

### Goal
Allow third-party extensions without modifying core.

### Foundation Complete ✅
The integration architecture provides the foundation for a plugin system with separate `FastMCPIntegration` and `CLIIntegration` classes.

### Ideas
- Plugin discovery via entry points
- Display type plugins
- State backend plugins
- Command namespace plugins

```python
# In setup.py/pyproject.toml
entry_points={
    "replkit2.displays": [
        "plotly = my_plugin:PlotlyDisplay",
    ]
}
```

## Future Release - Enhanced State Management

### Persistent State Backends
- SQLite adapter for command history and state
- Redis adapter for distributed state
- File watchers for auto-reload

### State Middleware
```python
@app.middleware
def audit_log(state, command, args, result):
    """Log all state modifications."""
    state.history.append({
        "command": command,
        "args": args,
        "timestamp": datetime.now()
    })
```


## Near Term - MCP Integration Refactoring (Phase 2)

### Goal
Reduce code duplication in MCP integration while maintaining backward compatibility.

### Planned Improvements
- Unify `_create_tool_wrapper` and `_create_prompt_wrapper` methods
- Extract common signature manipulation into `_create_mcp_signature` helper
- Consider adding prompt aliases (similar to tool aliases)
- Simplify wrapper creation logic

### Benefits
- Cleaner, more maintainable codebase
- Easier to extend with new features
- Consistent behavior across component types

## Future - Unified Registration System (Phase 3)

### Goal
Create a unified registration system for all MCP components (tools, resources, prompts).

### Design Concepts
```python
@dataclass
class Registration:
    name: str
    description: str
    component_type: ComponentType
    param_mapping: Optional[Dict[str, str]] = None
    uri_template: Optional[str] = None  # For resources
    is_alias: bool = False
```

### Challenges
- Resources have complex URI patterns (all-optional, greedy, stubs)
- Need to maintain backward compatibility
- Must handle parameter validation for resources

### Benefits
- Single source of truth for registration logic
- Resources could have aliases (with URI considerations)
- Reduced code duplication across component types
- Easier to add new component types

## Future Considerations

### Performance
- Async command support
- Streaming responses for large datasets
- Command result caching

### Developer Experience
- Built-in testing utilities
- Command replay/recording
- Interactive command builder

### Integration
- Jupyter notebook support
- VS Code extension
- Terminal UI mode (using Textual/Rich)

### Display Enhancements
- Color support (optional)
- Unicode box drawing (optional)
- Responsive table widths
- CSV/JSON export built-in

## Design Principles

1. **Backwards Compatibility** - New features should not break existing apps
2. **Progressive Enhancement** - Apps should work without optional features
3. **Type Safety** - All new APIs should be fully typed
4. **Minimal Dependencies** - Core should remain lightweight
5. **Extensible** - Users should be able to customize without forking

## Contributing

Ideas and feedback welcome! Please open an issue to discuss before implementing major features.

## Timeline

No fixed timeline. Features will be implemented based on:
- Community interest
- Maintainer availability  
- Technical feasibility
- Alignment with project goals

---

*Last updated: 2025-11-03*