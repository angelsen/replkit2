# PyDoV4 - Modern LSP REPL

**Note: PyDoV4 is a hero project/example application demonstrating ReplKit2's capabilities. It's not published to PyPI but serves as a comprehensive example of building complex REPL applications with ReplKit2.**

PyDoV4 is an interactive REPL for testing Language Server Protocol (LSP) features with Python language servers. Built on ReplKit2's modern patterns, commands return pure Python data structures and formatters handle presentation.

## Architecture

```
src/pydov4/
├── __init__.py
├── app.py              # Main app with LSPState dataclass
├── client.py           # AsyncLSPClient with thread-based event loop
├── constants.py        # Severity StrEnum and error handling utilities
├── converters.py       # Protocol converters for server compatibility (ruff, etc.)
├── formatter.py       # Minimal custom formatter with code diagnostics display
├── commands/           # Modern v3 commands with clean data returns
│   ├── __init__.py
│   ├── core.py         # Core connection and status commands
│   ├── workspace.py    # File management and editing commands
│   ├── diagnostics.py  # Diagnostics commands with custom code view
│   ├── navigation.py   # Code navigation commands
│   └── actions.py      # Code actions (quickfixes, refactoring)
└── server/             # Server configuration
    ├── __init__.py
    └── config.py
```

## Key Features

### ReplKit2 Best Practices
- **Pure Python data returns** - Commands return dicts/lists/strings, not LSP objects
- **Native TextKit displays** - Uses box, table, tree, list display types
- **Minimal custom formatters** - Only `custom:code_diagnostics` for inline diagnostics
- **Consistent error handling** - `empty_table()` and `empty_tree()` utilities
- **Type-safe enums** - `Severity` StrEnum instead of magic numbers
- **Flask-style registration** - `@app.command(display="table")` decorators

### Display Characteristics
- **ASCII-only output** - No emojis, maximum compatibility
- **Consistent 80-char width** - All displays respect `config.width`
- **Clean data structures** - Formatters handle all formatting
- **Composable components** - Uses TextKit's `compose()` and `hr()`

### Supported LSP Features
- ✅ Server connection management (basedpyright, ruff, pyright, pylsp)
- ✅ File operations (open, close, save, list, refresh)
- ✅ Diagnostics with inline code view (`view_diagnostics`)
- ✅ Code actions with organization by kind (`actions_by_kind`)
- ✅ Code navigation (goto line/symbol, hover, definition, find)
- ✅ Editing (single line edit, regex replace)
- ✅ Custom converters for server compatibility (ruff)
- ⚠️ Hover information (server-dependent)
- ⚠️ Go to definition (basic support)
- ❌ Completions (not implemented)
- ❌ Rename symbol (not implemented)
- ❌ Format document (not implemented)

## Usage

### Interactive REPL

```bash
# Run with the pydo command
pydo

# Or use Python module
uv run -m pydov4
```

### Quick Start

```python
# Connect to a language server
>>> connect()           # Default: basedpyright
>>> connect("ruff")     # Alternative: ruff

# Open a file
>>> open("test.py")
>>> open("src/main.py", 50)  # Jump to line 50

# View and navigate
>>> view()              # Show current file with diagnostics
>>> view(20, 15)        # Show 15 lines starting at line 20
>>> goto(100)           # Jump to line 100
>>> files()             # List all open files

# Check diagnostics
>>> diagnostics()       # Show all diagnostics in a table
>>> diagnostics("error") # Show only errors
>>> view_diagnostics()  # Show code with inline diagnostic markers
>>> refresh()           # Refresh diagnostics

# Code actions (quickfixes, refactoring, etc.)
>>> actions(14)         # List available actions for line 14
>>> actions(14, 10)     # Actions at specific column
>>> apply(1)            # Apply action #1 (limited by pygls)
>>> actions_by_kind()   # Show actions organized by kind (tree display)

# Edit code
>>> edit(5, "import os")  # Replace line 5
>>> replace(r"TODO:\s*", "FIXME: ", 10)  # Regex replace on line 10
>>> save()               # Save and notify LSP

# Server info
>>> status()            # Quick status
>>> status(verbose=True) # Detailed capabilities
>>> disconnect()        # Disconnect from server
```

## Display Examples

### Box Displays (80 chars)
```
+-- Server Connected ----------------------------------------------------------+
| Connected to ruff v0.12.1                                                    |
| Features: navigation, diagnostics, fixes, formatting                         |
+------------------------------------------------------------------------------+
```

### Table Displays (Native TextKit)
```
File       Line  Severity  Message                                 Source      
---------  ----  --------  --------------------------------------  ------------
app.py     31    warning   Module level import not at top of file  Ruff  
app.py     35    warning   `.commands` imported but unused         Ruff  
test.py    14    error     "json" is not defined                   basedpyright
```

### Code Diagnostics Display (Custom)
```
File: src/pydov4/app.py (lines 30-39)
--------------------------------------------------------------------------------
  30   | # Apply custom formatter for PyDoV4-specific formatting
  31 W | from .formatter import PyDoV4Formatter  # noqa: E402
       | ^ warning: Module level import not at top of file
  32   | app = app.using(PyDoV4Formatter())
  33   | 
  34   | # Import commands after app is created (they self-register)
  35 W | from . import commands  # noqa: E402, F401
       | ^ warning: Module level import not at top of file
       | ^ warning: `.commands` imported but unused
```

### Status Indicators
- `[OK]` - Connected
- `[X]` - Not connected  
- `[!]` - Has diagnostics
- `[+]` - No issues
- `>` - Current file marker

## Technical Details

### Thread-based Async Client
The core innovation is running the LSP client in a dedicated thread:

```python
def _run_async(self, coro):
    """Run a coroutine in the client's loop and return result."""
    future = asyncio.run_coroutine_threadsafe(coro, self.loop)
    return future.result(timeout=30.0)
```

This allows synchronous REPL commands to work with async LSP operations.

### Custom Formatter
PyDoV4 uses a minimal custom formatter that:
- Provides `custom:code_diagnostics` display for inline diagnostics
- Composes TextKit components (`compose()`, `hr()`, `box()`)
- Respects `config.width` for all displays
- Uses ASCII-only characters

### Protocol Converters
Special converters handle server-specific protocol quirks:
- Ruff's non-standard NotebookDocumentSyncOptions
- Custom cattrs converter factories for each server
- Automatic converter selection based on server name

## Configuration

To change the global display width:
```python
from replkit2.textkit import config
config.width = 100  # Set to 100 characters
```

All box displays will automatically use the new width.

## Limitations

1. **Action Preview Only** - Due to pygls limitations, code actions are shown but not applied
2. **Server Dependent** - Features like hover/definition depend on server support
3. **Single File Focus** - Primarily designed for single-file operations
4. **No Workspace Features** - No multi-file refactoring or project-wide search

## Development

To add new commands:
1. Create function in appropriate module in `commands/`
2. Import app and use `@app.command` decorator with display type
3. First parameter must be `state`
4. Return pure Python data structures (dict/list/str)
5. Use `empty_table()` or `empty_tree()` for error cases
6. Let the formatter handle all formatting

Example:
```python
from ..app import app
from ..constants import empty_table

@app.command(display="table", headers=["Name", "Type", "Line"])
def symbols(state):
    """List document symbols."""
    if not state.client.client or not state.current_file:
        return empty_table()
    
    # Return clean data, not LSP objects or formatted strings
    return [
        {"Name": "main", "Type": "function", "Line": "42"},
        {"Name": "Config", "Type": "class", "Line": "10"},
    ]
```

### Best Practices
- Always specify display type: `box`, `table`, `tree`, `list`
- Return consistent data shapes for each display type
- Use `Severity` enum instead of numeric values
- Let TextKit handle all visual formatting
- Create custom displays only when they add real value