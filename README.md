# ReplKit2

**Flask-style framework for building stateful REPL applications with rich ASCII output, multi-mode operation, and extensive integrations.**

[![PyPI version](https://badge.fury.io/py/replkit2.svg)](https://badge.fury.io/py/replkit2)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🚀 Multi-Mode Operation**: Write once, deploy as REPL, CLI, MCP server, or REST API
- **🎨 Rich Text Display**: Built-in formatters for tables, trees, boxes, charts, progress bars, and markdown
- **🔌 FastMCP Integration**: Automatic tool/resource/prompt registration for Claude Desktop, Continue.dev, etc.
- **⚡ Typer CLI Support**: Traditional command-line interfaces with help text and argument parsing  
- **📊 TextKit Rendering**: Powerful ASCII art generation with compose-based layouts
- **🔧 Extensible**: Custom display types, formatters, and integrations
- **💾 State Management**: Persistent state across commands with dataclass-based architecture
- **🎯 Type Safe**: Full type annotations with basedpyright support

## 🏃 Quick Start

### Installation

```bash
pip install replkit2
# or
uv add replkit2
```

### Basic Example

```python
from dataclasses import dataclass, field
from replkit2 import App

@dataclass
class AppState:
    tasks: list[dict] = field(default_factory=list)
    next_id: int = 1

app = App("todo", AppState)

@app.command(display="table", headers=["ID", "Task", "Done"])
def list_tasks(state):
    """List all tasks in table format."""
    return [{"ID": t["id"], "Task": t["text"], "Done": "✓" if t["done"] else "○"} 
            for t in state.tasks]

@app.command()
def add_task(state, text: str):
    """Add a new task."""
    task = {"id": state.next_id, "text": text, "done": False}
    state.tasks.append(task)
    state.next_id += 1
    return f"Added task #{task['id']}: {text}"

if __name__ == "__main__":
    app.run(title="Todo Manager")
```

**Run it:**
```bash
uv run todo.py           # Interactive REPL
uv run todo.py --cli     # Traditional CLI mode  
uv run todo.py --mcp     # MCP server for Claude
```

## 🎯 Multi-Mode Deployment

The same application code works across different interfaces:

### REPL Mode (Interactive)
```python
app.run(title="My App")
```
- Rich formatted output
- Interactive command prompt
- Auto-generated help system

### CLI Mode (Traditional)
```python
app.cli()
```
- Standard command-line interface
- `--help` for each command
- Argument parsing via Typer
- Works with shell pipes and scripts

### MCP Server Mode
```python
app.mcp.run()
```
- Exposes tools, resources, and prompts
- Compatible with Claude Desktop, Continue.dev
- Stateful between calls

### API Mode (REST)
```python
json_app = app.using(JSONFormatter())
# Use with FastAPI, Flask, etc.
```

## 🎨 Display Types

ReplKit2 includes built-in display formatters:

| Type | Input | Output |
|------|-------|--------|
| `table` | List of dicts/lists | Formatted table with headers |
| `box` | String | Bordered box with optional title |
| `tree` | Nested dict | Hierarchical tree view |
| `list` | List of strings | Bullet or numbered lists |
| `bar_chart` | Dict with numbers | Horizontal bar chart |
| `progress` | `{value, total}` | Progress bar with percentage |
| `markdown` | `{elements, frontmatter}` | Rich markdown with YAML metadata |

### Example: Multiple Display Types

```python
@app.command(display="progress", show_percentage=True)
def completion(state):
    done = sum(1 for t in state.tasks if t["done"])
    return {"value": done, "total": len(state.tasks)}

@app.command(display="tree")
def categorize(state):
    return {
        "pending": [t["text"] for t in state.tasks if not t["done"]],
        "completed": [t["text"] for t in state.tasks if t["done"]]
    }
```

## 🔌 FastMCP Integration

Expose your commands as MCP tools, resources, and prompts:

```python
# FastMCP Tool (actions)
@app.command(fastmcp={"type": "tool", "tags": ["productivity"]})
def add_task(state, text: str, priority: str = "normal"):
    """Add a new task with optional priority."""
    # Implementation...
    return f"Added task: {text}"

# FastMCP Resource (data access)
@app.command(fastmcp={"type": "resource", "mime_type": "application/json"})
def get_task(state, id: int):
    """Get task by ID - creates resource at app://get_task/{id}"""
    return next((t for t in state.tasks if t["id"] == id), None)

# FastMCP Prompt (context injection)
@app.command(fastmcp={"type": "prompt"})
def task_context(state, focus: str = None):
    """Generate context for task-related prompts."""
    recent_tasks = state.tasks[-5:]
    return f"Recent tasks: {recent_tasks}\nFocus: {focus}"
```

**Connect to Claude Desktop:**
```json
{
  "mcpServers": {
    "my-app": {
      "command": "uv",
      "args": ["run", "/path/to/your/app.py", "--mcp"]
    }
  }
}
```

**Connect to Claude Code:**
```bash
# Add to your MCP configuration
claude mcp add my-app "uv run /path/to/your/app.py --mcp"

# List connected servers
claude mcp list
```

## ⚡ Typer CLI Integration

Create traditional CLIs with the same commands:

```python
@app.command(
    display="table",
    headers=["ID", "Task", "Status"],
    typer={
        "name": "ls",  # CLI command name
        "help": "List all tasks with filtering options"
    }
)
def list_tasks(state, status: str = "all", limit: int = 10):
    """List tasks with optional filtering."""
    # Same implementation works for REPL, CLI, and MCP
    tasks = state.tasks
    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]
    return tasks[:limit]
```

**Usage:**
```bash
uv run todo.py ls --status pending --limit 5
uv run todo.py add "Buy groceries"
uv run todo.py --help
```

## 🛠️ Custom Display Types

Create reusable custom formatters:

```python
@app.formatter.register("dashboard")
def render_dashboard(data, meta, formatter):
    """Custom dashboard display with multiple sections."""
    from replkit2.textkit import compose, box
    from replkit2.types.core import CommandMeta
    
    # Use formatter to handle nested display types
    summary_meta = CommandMeta(display="box", title="Summary")
    tasks_meta = CommandMeta(display="table", headers=["ID", "Task"])
    
    summary = formatter.format(data["summary"], summary_meta)
    tasks = formatter.format(data["tasks"], tasks_meta)
    
    return compose(summary, tasks, spacing=1)

@app.command(display="dashboard")
def overview(state):
    return {
        "summary": f"Total: {len(state.tasks)} tasks",
        "tasks": [{"ID": t["id"], "Task": t["text"]} for t in state.tasks[:5]]
    }
```

## 📁 Examples

Comprehensive examples in `/examples/`:

- **[`todo.py`](examples/todo.py)** - Full task manager with state persistence
- **[`monitor.py`](examples/monitor.py)** - System monitoring dashboard  
- **[`notes_mcp.py`](examples/notes_mcp.py)** - FastMCP integration demo
- **[`typer_demo.py`](examples/typer_demo.py)** - CLI with JSON persistence
- **[`markdown_demo.py`](examples/markdown_demo.py)** - Markdown formatter showcase
- **[`formatter_demo.py`](examples/formatter_demo.py)** - Custom formatters
- **[`todo_api.py`](examples/todo_api.py)** - FastAPI REST integration

**Run examples:**
```bash
cd examples/
uv run todo.py               # Interactive REPL
uv run notes_mcp.py --mcp    # MCP server
uv run typer_demo.py --help  # CLI help
```

## 🏗️ Architecture

ReplKit2 follows a clean, extensible architecture:

```
src/replkit2/
├── app.py              # Main App class and command registration
├── integrations/       # Multi-mode deployment
│   ├── mcp.py         # FastMCP server integration  
│   └── cli.py         # Typer CLI integration
├── textkit/           # ASCII rendering system
│   ├── core.py        # Layout primitives (box, table, tree)
│   ├── formatter.py   # Display type system
│   └── markdown.py    # Markdown renderer
└── types/             # Type definitions
    └── core.py        # FastMCP and command metadata
```

## 🔧 Configuration

### FastMCP Options
```python
@app.command(fastmcp={
    "type": "tool",                  # tool | resource | prompt
    "tags": ["productivity"],        # Categorization tags
    "enabled": True,                 # Include in MCP server
    "stub": True,                    # Generate stub URIs for docs
    "mime_type": "application/json"  # Resource MIME type
})
```

### Typer Options  
```python
@app.command(typer={
    "name": "ls",              # CLI command name
    "help": "List items",      # Override help text
    "hidden": False,           # Hide from help
    "enabled": True,           # Include in CLI
    "rich_help_panel": "Core"  # Group in help
})
```

## 📚 Documentation

- **[Development Guide](CLAUDE.md)** - Type checking, patterns, best practices
- **[LLM Guide](src/replkit2/llms.txt)** - Comprehensive framework guide for AI assistants
- **[Examples README](examples/README.md)** - Detailed example walkthroughs
- **[TextKit Docs](src/replkit2/textkit/README.md)** - ASCII rendering system
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[Roadmap](ROADMAP.md)** - Future development plans

## 🤝 Contributing

1. **Type Safety**: Uses `basedpyright` with pragmatic configuration
2. **Code Style**: Run `ruff format` and `ruff check`
3. **Testing**: Examples serve as integration tests
4. **Documentation**: Keep LLM guides and examples updated

```bash
# Development setup
git clone https://github.com/user/replkit2
cd replkit2
uv install --dev

# Type checking
uv run basedpyright src/replkit2

# Code formatting  
uv run ruff format src/ examples/
uv run ruff check src/ examples/
```

## 🚀 Roadmap

- **v0.7.0**: FastAPI integration (REPL/CLI/MCP/API unified deployment)
- **v0.8.0**: Plugin system architecture
- **v0.9.0**: Enhanced state management with database backends
- **v1.0.0**: Production-ready with performance optimizations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Built With

- **[FastMCP](https://github.com/jlowin/fastmcp)** - Model Context Protocol server framework
- **[Typer](https://github.com/tiangolo/typer)** - CLI framework based on Python type hints
- **Custom TextKit** - Pure Python ASCII art rendering system

---

**Write once, deploy everywhere** - Build rich terminal applications that work as interactive REPLs, traditional CLIs, MCP servers, and REST APIs from a single codebase.