# Integration Architecture

ReplKit2 apps deploy in multiple modes from a single codebase. This guide explains integration patterns and when to use each.

## Core Concept

Write commands once:
```python
@app.command(display="table", headers=["ID", "Task"])
def list_tasks(state, status: str = "all"):
    """List tasks with optional status filter."""
    if status == "all":
        return state.tasks
    return [t for t in state.tasks if t["status"] == status]
```

Deploy everywhere:
- **REPL**: Interactive development environment
- **CLI**: Traditional command-line interface
- **MCP**: LLM tool server for Claude, Continue, etc.
- **API**: REST endpoints for web applications

## Integration Modes

### 1. REPL Mode

**Pattern**: `app.run()`

```python
if __name__ == "__main__":
    app.run(title="My Application")
```

**Features:**
- Commands available as Python functions
- Automatic formatting with TextFormatter
- Built-in `help()` command
- State preserved between commands

**Access:**
```python
>>> list_tasks()          # Execute command
>>> list_tasks("active")  # With arguments
>>> app.state.tasks       # Direct state access
>>> help()                # Show all commands
```

### 2. MCP Server Mode

**Pattern**: `app.mcp.run()`

```python
if "--mcp" in sys.argv:
    app.mcp.run()
```

**Configuration:**
```python
# Tool (action/command)
@app.command(fastmcp={"type": "tool"})
def add_task(state, task: str):
    return f"Added: {task}"

# Resource (readable data)
@app.command(fastmcp={"type": "resource"})
def get_task(state, id: int):
    return state.tasks[id]

# Prompt (template)
@app.command(fastmcp={"type": "prompt"})
def task_summary(state):
    return "\n".join(t["name"] for t in state.tasks)
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "myapp": {
      "command": "python",
      "args": ["/path/to/app.py", "--mcp"]
    }
  }
}
```

**Key points:**
- Commands must have MCP-compatible types (no Union, Optional defaults to None)
- Resources use URI patterns: `app://get_task/123`
- State persists across MCP calls

### 3. CLI Mode

**Pattern**: `app.cli()`

```python
if "--cli" in sys.argv:
    app.cli()
```

**Configuration:**
```python
@app.command(
    display="table",
    typer={"name": "ls", "help": "List all tasks"}
)
def list_tasks(state, status: str = "all"):
    return state.tasks
```

**Usage:**
```bash
python app.py --cli ls                   # List tasks
python app.py --cli ls --status=active  # With options
python app.py --cli add "Buy milk"       # Add task
python app.py --cli --help               # Show help
```

### 4. Programmatic Usage (APIs)

**Pattern**: `app.state` + `app.execute()`

For FastAPI, Flask, Django, or any web framework.

```python
from fastapi import FastAPI
from replkit2 import App

app = App("todo", TodoState)
api = FastAPI()

# Direct state access for reads
@api.get("/todos")
def list_todos():
    return app.state.todos

# Execute commands for writes
@api.post("/todos")
def create_todo(task: str, priority: str = "medium"):
    app.execute("add", task, priority)
    return app.state.todos[-1]
```

**Advanced: Formatted output**

Occasionally you need formatted text (e.g., ASCII reports):

```python
from fastapi.responses import PlainTextResponse

@api.get("/report/text", response_class=PlainTextResponse)
def text_report():
    # Get raw data
    data = app.execute("report")

    # Get command metadata
    _, meta = app._commands["report"]

    # Format using app's formatter
    return app.formatter.format(data, meta)
```

### 5. Context-Aware Commands

Commands can detect execution mode to adapt behavior. Add `_ctx: ExecutionContext = None`:

```python
from replkit2.types import ExecutionContext

@app.command(display="table", fastmcp={"type": "tool"})
def preview(state, file: str, limit: int = None, _ctx: ExecutionContext = None):
    # Smart defaults: compact for REPL, full for MCP/CLI
    if limit is None:
        limit = 5 if _ctx and _ctx.is_repl() else None
    return load_data(file)[:limit] if limit else load_data(file)
```

**Mode detection:** `_ctx.is_repl()`, `_ctx.is_mcp()`, `_ctx.is_cli()`, `_ctx.is_programmatic()`

**Use for:** Large datasets, different output per mode, interactive vs batch behavior.

**Deprecation (v0.13):** Decorator-level `truncate=` and `transforms=` are deprecated. Use element-level config with `_ctx` instead. Removed in v0.14.

## Integration Properties

### `app.state`
- **Type**: Your state class instance
- **Access**: Direct read/write
- **Use**: Quick reads, state inspection

```python
app.state.todos
app.state.config
```

### `app.mcp`
- **Type**: `FastMCP` server instance
- **Access**: Property (lazy-loaded)
- **Use**: `app.mcp.run()` to start MCP server

### `app.cli`
- **Type**: `Typer` instance
- **Access**: Property (lazy-loaded)
- **Use**: `app.cli()` to run CLI

### `app.execute()`
- **Signature**: `execute(command_name: str, *args, _ctx: ExecutionContext = None, **kwargs) -> Any`
- **Returns**: Raw command result (unformatted)
- **Use**: Programmatic command execution

```python
result = app.execute("add", "Task", priority="high")
stats = app.execute("stats")

# With explicit context
from replkit2.types import ExecutionContext
ctx = ExecutionContext.for_programmatic()
result = app.execute("preview", "file.csv", _ctx=ctx)
```

### `app.formatter`
- **Type**: `TextFormatter` (internal)
- **Access**: Public but rarely needed
- **Use**: Format data with display metadata (advanced)

```python
data = app.execute("stats")
_, meta = app._commands["stats"]
formatted = app.formatter.format(data, meta)
```

## Decision Matrix

| Use Case | Pattern | Why |
|----------|---------|-----|
| Interactive dev | `app.run()` | Exploration, testing, debugging |
| CLI tool | `app.cli()` | Traditional command-line UX |
| LLM integration | `app.mcp.run()` | Claude, Continue, Cline, etc. |
| REST API | `app.execute()` + `app.state` | Raw data for JSON responses |
| Web dashboard | `app.execute()` + `app.state` | Data for frontend rendering |
| Report generation | `app.formatter.format()` | ASCII output (rare) |
| Jupyter notebook | `app.execute()` | Programmatic access |
| Testing | `app.execute()` | Unit tests for commands |

## Multi-Mode Example

Complete example supporting all modes:

```python
#!/usr/bin/env python3
from dataclasses import dataclass, field
from replkit2 import App
import sys

@dataclass
class TodoState:
    todos: list = field(default_factory=list)
    next_id: int = 1

app = App("todo", TodoState)

@app.command(
    display="table",
    headers=["ID", "Task", "Done"],
    fastmcp={"type": "tool"},
    typer={"name": "ls"}
)
def list_tasks(state, status: str = "all"):
    """List all tasks."""
    if status == "all":
        return state.todos
    return [t for t in state.todos if t["status"] == status]

@app.command(
    fastmcp={"type": "tool"},
    typer={"help": "Add a new task"}
)
def add(state, task: str, priority: str = "medium"):
    """Add a task."""
    state.todos.append({
        "id": state.next_id,
        "task": task,
        "priority": priority,
        "done": False
    })
    state.next_id += 1
    return f"Added: {task}"

if __name__ == "__main__":
    if "--mcp" in sys.argv:
        app.mcp.run()              # MCP server
    elif "--cli" in sys.argv:
        app.cli()                   # CLI mode
    elif "--api" in sys.argv:
        # Programmatic usage example
        app.execute("add", "Test task")
        print(app.state.todos)
    else:
        app.run(title="Todo App")  # REPL mode
```

## State Management

```python
# Read state
todos = app.state.todos
stats = {"total": len(app.state.todos)}

# Modify state (direct)
app.state.todos.append(new_todo)

# Modify state (via command - recommended)
app.execute("add", "Task")

# Why prefer execute()?
# - Command validation logic
# - Consistent behavior across REPL/CLI/MCP
# - Side effects (logging, hooks, etc.)
```

## Best Practices

1. **Commands return data, not strings** - Let formatters handle presentation
2. **Use `app.execute()` for APIs** - Returns raw data structures
3. **Access `app.state` for reads** - Direct, fast, simple
4. **Prefer `execute()` for writes** - Validation, consistency, side effects
5. **Keep commands pure** - No side effects except state modifications
6. **Type all parameters** - Required for MCP compatibility
7. **Test programmatically** - Use `execute()` in unit tests

## See Also

- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [textkit-architecture.md](textkit-architecture.md) - Formatter internals
- [examples/dataset.py](../examples/dataset.py) - Context-aware commands
- [examples/todo_api.py](../examples/todo_api.py) - FastAPI integration
