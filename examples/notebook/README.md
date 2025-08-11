# 📓 ReplKit2 Notebook Examples

Define ReplKit2 apps directly in Jupyter notebooks using comment markers.

## 🚀 Quick Start

```bash
# Install notebook support
uv add replkit2[notebook]

# Run notebook as app (future)
uv run replkit2 --notebook app.ipynb          # REPL mode
uv run replkit2 --notebook app.ipynb --mcp    # MCP server
uv run replkit2 --notebook app.ipynb --cli    # CLI
```

## 🏷️ Markers

- `# replkit2: state` - State class definition
- `# replkit2: command <name>` - Command definition
- `# replkit2: continue` - Continue multi-cell command
- `# replkit2: <value>` - Parameter default (e.g., `None`, `False`, `10`)

## 📝 Pattern

```python
# replkit2: command add
add = {
    "display": "table",
    "fastmcp": {"type": "tool"},
    "cli": {"help": "Add item"},
}
text: str = input("Enter: ")  # replkit2: None
verbose: bool = True          # replkit2: False

# Command logic
state.items.append(text)
f"Added: {text}"  # Last expression is return value
```

## ✨ Benefits

- **🔬 Explore**: Test logic interactively in notebook
- **📌 Define**: Mark cells as commands with markers
- **🚢 Deploy**: Same notebook becomes REPL/CLI/MCP app
- **📚 Document**: Notebook serves as live documentation

## 📁 Files

- `app.ipynb` - Minimal example with all patterns