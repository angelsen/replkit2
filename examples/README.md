# ReplKit2 Examples

Flask-style REPL applications with rich ASCII output, MCP integration, and CLI support.

## Quick Start

```bash
# Install
uv add replkit2

# Run examples
uv run python examples/todo.py
uv run python examples/monitor.py
uv run python examples/notes.py

# Run with MCP server
uv run python examples/notes.py --mcp

# Run as CLI
uv run python examples/tasks.py add "Buy milk"
uv run python examples/tasks.py list
```

## Core Examples

### todo.py - Todo List Manager
Full-featured task management with multiple views:
- Table view for task lists
- Tree view for categorization  
- Progress bars for completion tracking
- Custom multi-section reports
- State persistence between commands

Key patterns: state management, display types, custom formatters

### monitor.py - System Monitor
Real-time system monitoring dashboard:
- System status in table format
- Memory usage breakdown
- CPU/Memory/Disk usage with progress bars
- Network stats and process list in tables
- Multi-section report with composed displays

Key patterns: external data integration, real-time updates, report formatter

### notes.py - Note-Taking with MCP Integration
Note-taking app with MCP tools, resources, prompts, and markdown display:
- Tools: `add`, `list`, `delete`, `update`
- Resources: `get`, `search` (URI patterns)
- Prompts: `summarize`, `review` (with message format)
- Context-aware `recent` command
- Markdown display with frontmatter and builder pattern
- Dual-mode: REPL or MCP server

Key patterns: MCP configuration, ExecutionContext, markdown display, message format

### dataset.py - Context-Aware Commands
Comprehensive demonstration of ExecutionContext:
- Mode detection: REPL, MCP, CLI, programmatic
- Context-aware defaults with user override
- Different data structures per execution mode
- Backward compatibility (commands without context)
- Transport type and metadata inspection

Key patterns: ExecutionContext usage, adaptive behavior, mode detection

### tasks.py - CLI with Persistent State
Task manager with CLI and JSON persistence:
- Typer CLI mode with traditional command-line interface
- Commands work in both REPL and CLI modes
- JSON persistence in `examples/data/todo-cli-state.json`
- Custom command names via `typer` parameter
- Multi-mode deployment pattern

Key patterns: Typer configuration, state persistence, multi-mode deployment

### todo_api.py - REST API Integration
Same todo app exposed as FastAPI:
- Shared state between REPL and API
- Direct command execution via `app.execute()`
- Programmatic state access pattern
- Swagger UI at `/docs`

Run: `uv run --extra api uvicorn examples.todo_api:app`

## Archived Examples

The `_archive/` directory contains examples that have been consolidated into core examples:

- **assistant.py** - MCP message format with elements content (→ notes.py: `review` command)
- **dashboard.py** - Custom formatter delegation patterns (→ todo.py: `handle_report` formatter)
- **report.py** - Markdown display features (→ notes.py: `report` and `review` commands)

These remain as reference for advanced patterns and comprehensive feature demonstrations.

## Command Patterns

### Basic Command
```python
@app.command()
def hello(state, name: str = "World"):
    return f"Hello, {name}!"
```

### Table Display
```python
@app.command(display="table", headers=["ID", "Task", "Done"])
def list_tasks(state):
    return [{"ID": t.id, "Task": t.text, "Done": "[X]" if t.done else "[ ]"} 
            for t in state.tasks]
```

### FastMCP Tool
```python
@app.command(fastmcp={"type": "tool", "tags": {"productivity"}})
def add_task(state, text: str):
    task = state.add_task(text)
    return f"Added task #{task.id}"
```

### Typer CLI Command
```python
@app.command(
    display="table",
    typer={"name": "ls", "help": "List all tasks"}
)
def list_tasks(state, done: bool = False):
    tasks = [t for t in state.tasks if not done or t.done]
    return [{"ID": t.id, "Task": t.text} for t in tasks]
```

### Context-Aware Command
```python
from replkit2.types import ExecutionContext

@app.command(display="table", fastmcp={"type": "tool"})
def preview(state, limit: int = None, _ctx: ExecutionContext = None):
    """Preview data with context-aware defaults."""
    # Smart defaults based on execution mode
    if limit is None:
        limit = 5 if _ctx and _ctx.is_repl() else None  # Full for MCP/CLI

    data = get_data(state)
    return data[:limit] if limit else data
```

### Custom Formatter
```python
@app.formatter.register("report")
def handle_report(data, meta, formatter):
    """Custom formatters receive (data, meta, formatter)."""
    sections = []
    for title, section_data, display_type in data:
        section_meta = CommandMeta(display=display_type)
        formatted = formatter.format(section_data, section_meta)
        sections.append(box(formatted, title=title))
    return compose(*sections, spacing=1)
```

## Running Modes

### REPL Mode (Default)
```python
app.run(title="My Application")
```
- Interactive command prompt
- Auto-generated help()
- Pretty-printed output

### CLI Mode (Typer)
```python
app.cli()
```
- Traditional command-line interface
- `--help` for each command
- Formatted output based on display type
- Works with persistent state (e.g., JSON files)

### MCP Server Mode
```python
app.mcp.run()
```
- Exposes tools/resources/prompts via MCP
- Compatible with Claude Desktop, Continue, etc.
- Stateful between calls

### Programmatic Usage (APIs, Web Frameworks)
```python
from replkit2.types import ExecutionContext

# Access state directly
state = app.state

# Execute commands and get raw data
result = app.execute("add", "Buy milk")
stats = app.execute("stats")

# Pass explicit context
ctx = ExecutionContext.for_programmatic()
result = app.execute("preview", _ctx=ctx)

# Use with FastAPI
@api.post("/todos")
def create_todo(todo: TodoCreate):
    app.execute("add", todo.task, todo.priority)
    return state.todos[-1]
```
- Commands return raw data structures
- Direct state access for reads
- Optional ExecutionContext for context-aware commands
- Ideal for REST APIs and web frameworks

## Display Types

| Type | Input Data | Output |
|------|------------|--------|
| `table` | List of dicts or list of lists | Formatted table with headers |
| `box` | String | Bordered box with optional title |
| `tree` | Nested dict | Hierarchical tree view |
| `list` | List of strings | Bullet list |
| `bar_chart` | Dict of numbers | Horizontal bar chart |
| `progress` | {value, total} | Progress bar |
| `markdown` | {elements, frontmatter} | Formatted markdown with Table/Alert elements |

## Configuration Options

### FastMCP Config
| Option | Purpose | Example |
|--------|---------|---------|
| `{"type": "tool"}` | Actions/commands | CLI-like operations |
| `{"type": "resource"}` | Readable data | `app://get_item/{id}` |
| `{"type": "prompt"}` | Prompt templates | Context injection |
| `{"enabled": False}` | Exclude from MCP | REPL-only commands |

### Typer Config
| Option | Purpose | Example |
|--------|---------|---------|
| `{"name": "cmd"}` | CLI command name | `list` → `ls` |
| `{"help": "text"}` | Override help text | Better CLI docs |
| `{"hidden": True}` | Hide from help | Admin commands |
| `{"enabled": False}` | Exclude from CLI | REPL-only commands |

## Tips

1. **State First**: Every command receives state as first parameter
2. **Return Data**: Commands return data, not formatted strings
3. **Display Hints**: Match return type to display type
4. **Multi-Mode**: Write once, run as REPL/CLI/MCP
5. **Type Safety**: Import types from `replkit2.types.core`
6. **Persistence**: Use JSON/pickle for CLI state between runs