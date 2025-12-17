# ReplKit2

Flask-style framework for building stateful REPL applications with rich display, MCP integration, and multi-mode deployment.

## ✨ Features

- 🚀 **Multi-mode**: REPL, CLI, MCP server, API integration from one codebase
- 🎨 **Rich display**: Tables, trees, boxes, charts, markdown
- 🔌 **MCP ready**: Tools, resources, prompts for Claude/LLMs
- ⚡ **CLI support**: Traditional command-line interface via Typer
- 🌐 **API integration**: Programmatic access for FastAPI, Flask, etc.
- 🎯 **Type safe**: Full type hints, MCP-compatible validation

## 📦 Installation

```bash
# With uv (recommended)
uv add replkit2                      # Core library only
uv add "replkit2[all]"               # MCP + CLI support
uv add "replkit2[mcp,cli]"           # Same as above
uv add "replkit2[examples]"          # For running examples

# Or with pip
pip install replkit2
pip install replkit2[all]            # MCP + CLI support
pip install replkit2[mcp,cli]        # Same as above
pip install replkit2[examples]       # For running examples
```

## 🚀 Quick Start

```python
from dataclasses import dataclass, field
from replkit2 import App

@dataclass
class State:
    tasks: list = field(default_factory=list)
    next_id: int = 1

app = App("todo", State)

@app.command(display="table", headers=["ID", "Task", "Done"])
def list_tasks(state):
    """List all tasks."""
    return [{"ID": t["id"], "Task": t["text"], "Done": "✓" if t["done"] else ""} 
            for t in state.tasks]

@app.command()
def add(state, text: str):
    """Add a task."""
    task = {"id": state.next_id, "text": text, "done": False}
    state.tasks.append(task)
    state.next_id += 1
    return f"Added: {text}"

@app.command()
def done(state, id: int):
    """Mark task as done."""
    for task in state.tasks:
        if task["id"] == id:
            task["done"] = True
            return f"Completed task {id}"
    return f"Task {id} not found"

if __name__ == "__main__":
    import sys
    if "--mcp" in sys.argv:
        app.mcp.run()     # MCP server for Claude/LLMs
    elif "--cli" in sys.argv:
        app.cli()         # Traditional CLI
    else:
        app.run(title="Todo Manager")  # Interactive REPL
```

**Run it:**
```bash
python todo.py                    # Interactive REPL
python todo.py --cli add "Buy milk"  # CLI mode
python todo.py --cli list_tasks      # CLI mode
python todo.py --mcp              # MCP server
```

## 🎨 Display Types

```python
@app.command(display="table", headers=["Name", "Status"])
def show_table(state):
    return [{"Name": "Item 1", "Status": "Active"}]

@app.command(display="box", title="Info")
def show_box(state):
    return "This is in a box!"

@app.command(display="tree")
def show_tree(state):
    return {"root": {"child1": "leaf", "child2": ["item1", "item2"]}}

@app.command(display="progress", show_percentage=True)
def show_progress(state):
    return {"value": 7, "total": 10}

@app.command(display="markdown")
def show_markdown(state):
    return {
        "elements": [
            {"type": "heading", "content": "Status Report"},
            {"type": "alert", "content": "System is operational", "level": "success"},
            {"type": "table", "headers": ["Task", "Status"], 
             "rows": [{"Task": "Backup", "Status": "Complete"}]},
        ]
    }
```

## 🔌 MCP Integration

```python
# Tool (callable action)
@app.command(fastmcp={"type": "tool"})
def process(state, text: str, count: int = 1):
    return f"Processed '{text}' {count} times"

# Resource (readable data at app://get_task/123)
@app.command(fastmcp={"type": "resource"})
def get_task(state, id: int):
    return {"id": id, "data": state.tasks.get(id)}

# Prompt template
@app.command(fastmcp={"type": "prompt"})
def brainstorm(state, topic: str = ""):
    context = "\n".join(t["text"] for t in state.tasks[:5])
    return f"Based on these tasks:\n{context}\n\nBrainstorm about: {topic}"
```

Configure Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "todo": {
      "command": "python",
      "args": ["/path/to/todo.py", "--mcp"]
    }
  }
}
```

## ⚡ CLI Support

```python
@app.command(
    typer={"name": "ls", "help": "List tasks with filters"}
)
def list_tasks(state, done: bool = False, limit: int = 10):
    tasks = [t for t in state.tasks if not done or t.get("done")]
    return tasks[:limit]

# Usage:
# python todo.py --cli ls --done --limit 5
# python todo.py --cli add "New task"
# python todo.py --cli done 1
```

## 🌐 Multi-Mode Deployment

Write once, deploy everywhere - REPL, CLI, MCP server, or programmatic API:

```python
if __name__ == "__main__":
    import sys
    if "--mcp" in sys.argv:
        app.mcp.run()           # MCP server for Claude/LLMs
    elif "--cli" in sys.argv:
        app.cli()               # Traditional CLI
    else:
        app.run(title="My App") # Interactive REPL
```

**Integration properties:** `app.mcp` (MCP server), `app.cli` (CLI), `app.state` (direct access), `app.execute()` (programmatic)

See [`docs/integrations.md`](docs/integrations.md) for complete integration patterns and web framework examples.

## 🎭 Context-Aware Commands

Commands can detect execution mode (REPL, MCP, CLI, programmatic) and adapt behavior accordingly:

```python
from replkit2.types import ExecutionContext

@app.command(display="table", fastmcp={"type": "tool"})
def preview(state, file: str, limit: int = None, _ctx: ExecutionContext = None):
    """Preview with smart defaults based on execution mode."""
    if limit is None:
        limit = 5 if _ctx and _ctx.is_repl() else None  # Compact for REPL, full for MCP/CLI
    return load_file(state, file)[:limit] if limit else load_file(state, file)
```

**When to use:** Commands with large datasets or different output needs per mode.
**Key features:** Opt-in, auto-injected, backward compatible, user override.

See [`docs/integrations.md`](docs/integrations.md) for complete guide.

## 🎯 Type Safety

```python
# ✅ Good - MCP compatible
def cmd(state, 
    required: str,                  # Required param
    optional: str = None,           # Optional with None
    items: List[str] = None,        # Typed list
    config: Dict[str, int] = None,  # Typed dict
):
    pass

# ❌ Bad - causes "unknown" in MCP
def cmd(state,
    untyped,                        # Missing annotation
    opt: Optional[str] = None,      # Don't use Optional
    either: Union[str, int] = "",   # Don't use Union
):
    pass
```

## 📁 Examples

- **[`todo.py`](examples/todo.py)** - Full task manager with persistence
- **[`notes.py`](examples/notes.py)** - Note-taking with MCP integration
- **[`dataset.py`](examples/dataset.py)** - Context-aware commands
- **[`monitor.py`](examples/monitor.py)** - System monitoring dashboard
- **[`tasks.py`](examples/tasks.py)** - CLI with JSON state
- **[`todo_api.py`](examples/todo_api.py)** - FastAPI integration

Run examples:
```bash
cd examples
python todo.py                  # REPL mode
python dataset.py               # Context-aware demo
python notes.py --mcp           # MCP server
python tasks.py --cli --help    # CLI help
```

## 📚 Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [ROADMAP.md](ROADMAP.md) - Future plans
- [docs/integrations.md](docs/integrations.md) - Multi-mode deployment guide
- [src/replkit2/llms.txt](src/replkit2/llms.txt) - LLM quick reference

## 🛠️ Development

```bash
# Clone and install
git clone https://github.com/angelsen/replkit2
cd replkit2
uv sync --group dev

# Type check
uv run basedpyright src/replkit2

# Format & lint
uv run ruff format src/
uv run ruff check src/
```

## 📄 License

MIT - see [LICENSE](LICENSE) for details.