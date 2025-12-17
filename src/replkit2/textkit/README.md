# TextKit

ASCII display toolkit bundled with ReplKit2.

## Core Components

- **Display**: `box`, `table`, `tree`, `list_display`
- **Charts**: `bar_chart`, `progress`
- **Layout**: `compose`, `hr`, `align`, `wrap`
- **Markdown**: `markdown` builder and `MarkdownElement` base class
- **Config**: Global width setting (default 80)

## Basic Usage

```python
from replkit2.textkit import box, table, tree, compose

# box() expects string content
print(box("Hello, World!", title="Greeting"))

# table() expects list[list[Any]] - convert dicts if needed
data = [
    ["Alice", 30, "Engineering"],
    ["Bob", 25, "Design"],
]
print(table(data, headers=["Name", "Age", "Dept"]))

# Or convert from dicts manually
dict_data = [
    {"name": "Alice", "age": 30, "dept": "Engineering"},
    {"name": "Bob", "age": 25, "dept": "Design"},
]
rows = [[d["name"], d["age"], d["dept"]] for d in dict_data]
print(table(rows, headers=["Name", "Age", "Dept"]))

# tree() expects dict[str, Any]
org = {
    "Engineering": ["Alice", "Charlie"],
    "Design": ["Bob", "Dana"],
    "Sales": ["Eve"]
}
print(tree(org))

# Compose multiple displays
print(compose(
    box("5 users online", title="Status"),
    table(data, headers=["Name", "Age", "Dept"]),
    spacing=1
))
```

## Charts and Progress

```python
from replkit2.textkit import bar_chart, progress

# Bar chart
stats = {"Python": 85, "JavaScript": 60, "Go": 40}
print(bar_chart(stats, width=50, show_values=True))

# Progress bar
print(progress(75, 100, width=50, label="Processing"))
```

## ReplKit2 Integration

TextKit powers ReplKit2's default text formatter. Commands return data structures,
and the formatter automatically converts them to ASCII displays:

```python
from replkit2 import App

app = App("myapp", MyState)

# Formatter handles dict-to-table conversion automatically
@app.command(display="table", headers=["ID", "Name"])
def list_items(state):
    return [{"ID": 1, "Name": "Item"}]  # Returns list[dict]

# For programmatic use (APIs, web frameworks), use execute()
result = app.execute("list_items")  # Returns raw data (list[dict])
```

For direct textkit usage in custom formatters, see [`docs/textkit-architecture.md`](../../docs/textkit-architecture.md).

## Custom Display Handlers

Formatters receive `(data, meta, formatter)` and are **pure** - they only control presentation, not data selection.

```python
# Register custom display type
@app.formatter.register("custom")
def handle_custom(data, meta, formatter):
    """Custom display handlers receive data, meta, formatter.

    Note: Formatters do NOT receive ExecutionContext (v0.13.0+).
    Commands control data selection (context-aware), formatters control
    presentation (mode-agnostic). This maintains clean separation of concerns.
    """
    from replkit2.textkit import box, compose
    from replkit2.types.core import CommandMeta

    # Can reuse formatter for nested data transformation
    if isinstance(data["content"], list):
        content_meta = CommandMeta(display="list")
        content = formatter.format(data["content"], content_meta)
    else:
        content = data["content"]

    return compose(
        box(data["title"], title="Custom"),
        content
    )

@app.command(display="custom")
def custom_view(state):
    return {"title": "Hello", "content": "World"}
```

**Design principle (v0.13.0+):** Commands handle context-aware logic (what data to return), formatters stay pure (how to display it). For context-aware commands, see `examples/dataset.py`.

## Configuration

```python
from replkit2.textkit import config

# Change global width (affects all displays)
config.width = 100
```

## Markdown Generation

Generate formatted markdown with frontmatter and elements:

```python
from replkit2.textkit import markdown, MarkdownElement

# Using builder
doc = (markdown()
    .frontmatter(title="My Document", author="Me")
    .heading("Introduction")
    .text("This is a markdown document.")
    .code_block("print('Hello, World!')", language="python")
    .blockquote("Important note here")
    .list(["First item", "Second item"], ordered=True)
    .build())

# Returns dict with 'elements' and 'frontmatter' fields
# Use with display="markdown" in ReplKit2 commands
```

### Custom Markdown Elements

Create custom elements by subclassing `MarkdownElement`:

```python
class Admonition(MarkdownElement):
    element_type = "admonition"  # Auto-registers when class is defined
    
    def __init__(self, content: str, kind: str = "note"):
        self.content = content
        self.kind = kind
    
    @classmethod
    def from_dict(cls, data: dict) -> "Admonition":
        return cls(data.get("content", ""), data.get("kind", "note"))
    
    def render(self) -> str:
        return f"!!! {self.kind}\n    {self.content}"

# Use generic element() method for custom types
doc = markdown().element("admonition", content="Custom element", kind="tip").build()
```

## Philosophy

- ASCII-only output for maximum compatibility
- Bundled with ReplKit2, not a separate package
- Display functions return strings
- Composable and extensible
- Self-registering element system for markdown