# PyDoV4 Roadmap

This roadmap outlines the current state and planned features for PyDoV4, a clean-architecture LSP REPL built on ReplKit2.

## Current State (v0.4)

### ✅ Implemented Features

#### Core Infrastructure
- [x] Thread-based async LSP client
- [x] ReplKit2 integration with custom formatter
- [x] ASCII-only display output
- [x] Fixed-width table formatting
- [x] Cell wrapping support
- [x] Global width configuration via `config.width`
- [x] Protocol converters for server compatibility

#### Connection Management
- [x] `connect(server)` - Support for basedpyright, ruff, pyright, pylsp
- [x] `disconnect()` - Clean disconnection
- [x] `status(verbose)` - Connection status with capabilities

#### File Operations
- [x] `open(path, goto_line)` - Open with optional line jump
- [x] `close(path)` - Close files
- [x] `files()` - List open files with issue counts
- [x] `save()` - Save notification to LSP

#### Code Viewing
- [x] `view(start, count)` - Table display with diagnostics
- [x] `goto(line)` - Jump to line
- [x] `goto("def:symbol")` - Basic symbol search

#### Editing
- [x] `edit(line, content)` - Single line replacement
- [x] `replace(pattern, replacement, line)` - Regex replacement

#### Diagnostics
- [x] `diagnostics(severity, path)` - Filter by severity
- [x] `refresh()` - Manual refresh
- [ ] ~~`fix(line)`~~ - Being replaced by proper code actions
- [ ] ~~`fix_all()`~~ - Being replaced by proper code actions

#### Partial Support
- [x] `hover(line, col)` - Server-dependent
- [x] `definition(line, col)` - Limited support
- [x] `find(query, type)` - Basic implementation

## Recently Completed

### ✅ Code Actions (v0.5)
Successfully refactored from fix-centric approach to comprehensive code actions:
- `actions(line, col)` - List ALL available code actions
- `apply(number)` - Apply action by number (preview only due to pygls)
- `actions_at_cursor()` - Tree view organized by kind
- Supports all LSP action types: quickfix, refactor, source
- Consistent "actions" column showing counts across all tables

## Planned Features

### Phase 1: Core LSP Features (High Priority)

#### ~~1.1 Code Actions~~ ✅ (Completed in v0.5)
See "Recently Completed" section above.

#### 1.2 Code Completion
```python
@command(display="table", headers=["text", "kind", "detail"])
def complete(self, line: int, col: int, prefix: str = ""):
    """Get code completions at position.
    
    Returns completions with:
    - text: The completion text
    - kind: Type of completion (function, variable, etc)
    - detail: Additional information
    """
```

#### 1.3 Rename Symbol
```python
@command(display="box", title="Rename Preview")
def rename(self, line: int, col: int, new_name: str):
    """Rename symbol across all files.
    
    Shows preview of all changes before applying.
    """
```

#### 1.4 Find References
```python
@command(display="table", headers=["file", "line", "preview"])
def references(self, line: int, col: int):
    """Find all references to symbol at position."""
```

#### 1.5 Format Document
```python
@command(display="box", title="Format Result")
def format(self, path: str = None):
    """Format entire document using server's formatter."""
```

#### 1.6 Format Selection
```python
@command(display="box", title="Format Range")
def format_range(self, start_line: int, end_line: int):
    """Format selected line range."""
```

### Phase 2: Enhanced Navigation (Medium Priority)

#### 2.1 Workspace Symbols
```python
@command(display="table", headers=["name", "kind", "file", "line"])
def symbols(self, query: str = "", kind: str = None):
    """Search symbols across workspace.
    
    Args:
        query: Symbol name pattern
        kind: Filter by kind (function, class, variable)
    """
```

#### 2.2 Document Outline
```python
@command(display="tree")
def outline(self):
    """Show document structure as tree.
    
    Returns hierarchical view of classes, methods, etc.
    """
```

#### 2.3 Signature Help
```python
@command(display="box", title="Signature")
def signature(self, line: int, col: int):
    """Show function signature at call site."""
```

#### 2.4 Code Lens
```python
@command(display="table", headers=["line", "title", "command"])
def codelens(self):
    """Show available code lens actions.
    
    Includes test runners, reference counts, etc.
    """
```

#### 2.5 Inlay Hints
```python
@command(display="table", headers=["line", "col", "hint", "kind"])
def hints(self, enable: bool = True):
    """Toggle or show inlay hints.
    
    Shows type annotations, parameter names, etc.
    """
```

### Phase 3: Multi-file & Workspace (Lower Priority)

#### 3.1 Workspace Management
```python
@command(display="box", title="Workspace")
def open_folder(self, path: str):
    """Open entire folder as workspace."""

@command(display="tree")
def workspace_tree(self):
    """Show workspace file tree."""
```

#### 3.2 Multi-file Search
```python
@command(display="table", headers=["file", "line", "match"])
def search(self, pattern: str, file_pattern: str = "*.py"):
    """Search text across workspace files."""
```

#### 3.3 Call Hierarchy
```python
@command(display="tree")
def callers(self, line: int, col: int):
    """Show incoming calls to function."""

@command(display="tree")
def callees(self, line: int, col: int):
    """Show outgoing calls from function."""
```

### Phase 4: Advanced Features

#### 4.1 ~~Interactive Fix Selection~~ (Handled by Code Actions)
Fix selection is now part of the unified code actions system:
- Use `actions()` to list all available actions
- Use `apply(number)` to apply selected action

#### 4.2 Diagnostic Navigation
```python
@command(display="box")
def next_error(self, severity: str = None):
    """Jump to next diagnostic."""

@command(display="box")
def prev_error(self, severity: str = None):
    """Jump to previous diagnostic."""

@command(display="table", headers=["file", "line", "severity", "message"])
def all_errors(self):
    """List all diagnostics across workspace."""
```

#### 4.3 ~~Refactoring Support~~ (Handled by Code Actions)
Refactorings are now part of the unified code actions system:
- Use `actions()` to see all refactorings
- Use `apply()` to apply them
- Includes: extract method/variable, inline, move, etc.

#### 4.4 Progress & Tasks
```python
@command(display="table", headers=["id", "title", "progress", "message"])
def tasks(self):
    """Show running LSP server tasks."""

@command
def cancel_task(self, task_id: str):
    """Cancel a running task."""
```

### Phase 5: Infrastructure Improvements

#### 5.1 Configuration Management
```python
@command(display="table", headers=["key", "value", "description"])
def config_list(self):
    """List all server configuration options."""

@command
def config_set(self, key: str, value: Any):
    """Set server configuration value."""
```

#### 5.2 Multi-server Support
```python
@command(display="table", headers=["name", "status", "files"])
def servers(self):
    """List all connected servers."""

@command
def switch_server(self, name: str):
    """Switch active server."""
```

#### 5.3 Export/Import
```python
@command
def export_diagnostics(self, path: str, format: str = "json"):
    """Export diagnostics to file."""

@command
def export_symbols(self, path: str):
    """Export workspace symbols."""
```

#### 5.4 History & Persistence
```python
@command(display="table", headers=["time", "command", "result"])
def history(self, count: int = 10):
    """Show command history."""

@command
def save_session(self, name: str):
    """Save current session state."""

@command
def load_session(self, name: str):
    """Load saved session."""
```

## Implementation Guidelines

### Command Design
1. Follow ReplKit2 pattern - return data, not strings
2. Use appropriate display hints (table, box, tree, list)
3. Handle errors gracefully with clear messages
4. Check server capabilities before attempting operations

### Display Conventions
- Tables for structured data (diagnostics, symbols, etc)
- Boxes for status messages and previews
- Trees for hierarchical data (outline, call hierarchy)
- Lists for simple selections

### ASCII Indicators
- `[OK]` / `[X]` - Success/failure status
- `[!]` / `[+]` - Has issues / No issues
- `>` - Current/selected item
- `Y` / `-` - Yes/No or Available/Unavailable
- `E` / `W` / `I` / `H` - Error/Warning/Info/Hint

### Testing Strategy
1. Test with multiple servers (basedpyright, ruff, pyright, pylsp)
2. Handle missing capabilities gracefully
3. Ensure consistent display formatting
4. Verify data accuracy over presentation

## Success Metrics

- **Phase 1 Complete**: Core editing workflow functional
- **Phase 2 Complete**: Full code navigation capabilities
- **Phase 3 Complete**: Multi-file project support
- **Phase 4 Complete**: Advanced IDE-like features
- **Phase 5 Complete**: Production-ready tool

## Notes

- Priority based on user impact and implementation complexity
- Server compatibility varies - design for graceful degradation
- Focus on data quality - let formatters handle presentation
- Maintain clean separation between async client and sync commands