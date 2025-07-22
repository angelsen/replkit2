# ReplKit2 Examples

Flask-style REPL applications with rich ASCII output and MCP integration.

## Quick Start

```bash
# Install
uv add replkit2

# Run examples
uv run python examples/todo.py
uv run python examples/monitor.py
uv run python examples/notes_mcp.py

# Run with MCP
uv run python examples/notes_mcp.py --mcp
```

## Core Examples

### todo.py - Todo List Manager
Full-featured task management with multiple views:
- Table view for task lists
- Tree view for categorization
- Progress bars for completion tracking
- Custom multi-section reports
- State persistence between commands

Key patterns: state management, display types, custom display handlers

### monitor.py - System Monitor
Real-time system monitoring dashboard:
- CPU/Memory/Disk usage with progress bars
- Network stats in tables
- Process list with sorting
- Bar charts for resource visualization

Key patterns: external data integration, real-time updates, charts

### notes_mcp.py - FastMCP Integration Demo
Note-taking app exposing MCP tools, resources, and prompts:
- Tools: `add_note`, `list_notes`
- Resources: `note_summary`, `get_note/{id}` 
- Prompts: `brainstorm_prompt`
- Dual-mode: REPL or MCP server

Key patterns: FastMCP configuration, URI templates, typed configs

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
    return [{"ID": t.id, "Task": t.text, "Done": "✓" if t.done else "✗"} 
            for t in state.tasks]
```

### FastMCP Tool
```python
@app.command(fastmcp={"type": "tool", "tags": {"productivity"}})
def add_task(state, text: str):
    task = state.add_task(text)
    return f"Added task #{task.id}"
```

### FastMCP Resource
```python
@app.command(fastmcp={"type": "resource", "mime_type": "application/json"})
def task_stats(state):
    # Auto-generates URI: app://task_stats
    return {"total": len(state.tasks), "done": sum(1 for t in state.tasks if t.done)}
```

## Running Modes

### REPL Mode (Default)
```python
app.run(title="My Application")
```
- Interactive command prompt
- Auto-generated help()
- Pretty-printed output

### MCP Server Mode
```python
if "--mcp" in sys.argv:
    app.mcp.run()
```
- Exposes tools/resources/prompts via MCP
- Compatible with Claude Desktop, Continue, etc.
- Stateful between calls

### API Mode
```python
json_api = app.using(JSONFormatter())
# Use with FastAPI/Flask/etc
```
- Same commands, JSON output
- RESTful endpoints
- Shared state with REPL

## Display Types

| Type | Input Data | Output |
|------|------------|--------|
| `table` | List of dicts | Formatted table with headers |
| `box` | Any | Bordered box with optional title |
| `tree` | Nested dict | Hierarchical tree view |
| `list` | List | Bullet list |
| `bar_chart` | Dict of numbers | Horizontal bar chart |
| `progress` | {value, total} | Progress bar |

## FastMCP Types

| Config | Purpose | Example URI |
|--------|---------|-------------|
| `{"type": "tool"}` | Actions/commands | N/A |
| `{"type": "resource"}` | Readable data | `app://get_item/{id}` |
| `{"type": "prompt"}` | Prompt templates | N/A |
| `{"enabled": False}` | REPL-only command | N/A |

## Tips

1. **State First**: Every command receives state as first parameter
2. **Return Data**: Commands return data, not formatted strings
3. **Display Hints**: Match return type to display type
4. **MCP URIs**: Auto-generated from function name and parameters
5. **Type Safety**: Use `FastMCPTool`, `FastMCPResource` for IDE support