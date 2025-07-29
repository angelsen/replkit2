# ReplKit2 Examples

Flask-style REPL applications with rich ASCII output, MCP integration, and CLI support.

## Quick Start

```bash
# Install
uv add replkit2

# Run examples
uv run python examples/todo.py
uv run python examples/monitor.py
uv run python examples/notes_mcp.py

# Run with MCP server
uv run python examples/notes_mcp.py --mcp

# Run as CLI
uv run python examples/typer_demo.py add "Buy milk"
uv run python examples/typer_demo.py list
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

### notes_mcp.py - FastMCP Integration Demo
Note-taking app exposing MCP tools, resources, and prompts:
- Tools: `add_note`, `list_notes`
- Resources: `note_summary`, `get_note/{id}` 
- Prompts: `brainstorm_prompt`
- Dual-mode: REPL or MCP server

Key patterns: FastMCP configuration, URI templates, typed configs

### typer_demo.py - Typer CLI Integration Demo
Todo app with CLI, REPL, and persistent JSON state:
- Typer CLI mode with traditional command-line interface
- Commands work in both REPL and CLI modes
- JSON persistence in `examples/data/todo-cli-state.json`
- Custom command names and help text via `typer` parameter
- Shows the "write once, deploy everywhere" pattern

Key patterns: Typer configuration, state persistence, multi-mode deployment

### markdown_demo.py - Markdown Formatter Demo
Showcases the markdown display type:
- YAML frontmatter for metadata
- Standard markdown elements (headings, code blocks, lists, etc.)
- Custom element creation with auto-registration
- Builder pattern for fluent document construction
- Integration with other display types

Key patterns: markdown builder, custom MarkdownElement subclassing

### formatter_demo.py - Custom Formatter Examples
Demonstrates advanced formatter patterns:
- Dashboard display with multiple sections
- Formatter composition for nested data
- Direct textkit vs formatter comparison
- Reusable custom display types

Key patterns: formatter parameter usage, display composition

### todo_api.py - REST API Integration
Same todo app exposed as FastAPI:
- Shared state between REPL and API
- JSON formatting for API responses
- Swagger UI at `/docs`
- Demonstrates `app.using(JSONFormatter())`

Run: `uv run --extra api uvicorn examples.todo_api:app`

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

### API Mode
```python
json_app = app.using(JSONFormatter())
# Use with FastAPI/Flask/etc
```
- Same commands, JSON output
- RESTful endpoints
- Shared state with REPL

## Display Types

| Type | Input Data | Output |
|------|------------|--------|
| `table` | List of dicts or list of lists | Formatted table with headers |
| `box` | String | Bordered box with optional title |
| `tree` | Nested dict | Hierarchical tree view |
| `list` | List of strings | Bullet list |
| `bar_chart` | Dict of numbers | Horizontal bar chart |
| `progress` | {value, total} | Progress bar |
| `markdown` | {elements, frontmatter} | Formatted markdown with YAML frontmatter |

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