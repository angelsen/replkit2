# ReplKit2 Roadmap

## Overview

This document outlines potential future features and enhancements for ReplKit2. Items are not commitments but rather ideas under consideration. Community feedback is welcome via GitHub issues.

## Current Release - MCP Tool Aliases (Phase 1) ✅

### Completed in v0.7.3
Semantic aliases for MCP tools with parameter remapping support.

```python
@app.command(fastmcp={
    "type": "tool",
    "aliases": [
        {"name": "write", "description": "Write message", "param_mapping": {"command": "message"}},
        "exec",  # Simple alias
    ]
})
def execute(state, command: str): ...
```

### Benefits
- Natural language aliases for LLM interactions
- Parameter name remapping for semantic clarity
- Custom descriptions per alias
- Backward compatible

## Next Minor Version - FastAPI First-Class Support

### Goal
Enable ReplKit2 commands to automatically become API endpoints, similar to the existing FastMCP and Typer integrations.

### Foundation Complete ✅
As of v0.6.0, the integration architecture provides a solid foundation for adding FastAPI support alongside existing MCP and CLI integrations.

### Proposed API
```python
@app.command(
    display="table",
    api={"method": "GET", "path": "/tasks", "response_model": TaskList}
)
def list_tasks(state, status: str = None):
    return [t for t in state.tasks if not status or t["status"] == status]

# Integration
fastapi_app.include_router(app.api(), prefix="/replkit")
```

### Benefits
- Write once, deploy as REPL/CLI/MCP/API
- Automatic OpenAPI documentation
- Type-safe request/response handling
- Seamless integration with existing FastAPI projects

### Considerations
- Should we support Flask too via `app.flask_api()`?
- How to handle authentication/authorization?
- Response model generation from return types?

## Future Release - Plugin System

### Goal
Allow third-party extensions without modifying core.

### Foundation Complete ✅
As of v0.6.0, the integration architecture provides the foundation for a plugin system with separate `FastMCPIntegration` and `CLIIntegration` classes.

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

*Last updated: 2025-08-10*