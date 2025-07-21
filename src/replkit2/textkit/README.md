# TextKit

ASCII display toolkit bundled with ReplKit2.

## Core Components

- **Display**: `box`, `table`, `tree`, `list_display`
- **Charts**: `bar_chart`, `progress`
- **Layout**: `compose`, `hr`, `align`, `wrap`
- **Config**: Global width setting (default 80)

## Basic Usage

```python
from replkit2.textkit import box, table, tree, compose

# Simple box
print(box("Hello, World!", title="Greeting"))

# Table with data
data = [
    {"name": "Alice", "age": 30, "dept": "Engineering"},
    {"name": "Bob", "age": 25, "dept": "Design"},
]
print(table(data, headers=["name", "age", "dept"]))

# Tree structure
org = {
    "Engineering": ["Alice", "Charlie"],
    "Design": ["Bob", "Dana"],
    "Sales": ["Eve"]
}
print(tree(org))

# Compose multiple displays
print(compose(
    box("5 users online", title="Status"),
    table(data, headers=["name", "age", "dept"]),
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

TextKit is the default serializer for ReplKit2:

```python
from replkit2 import App

# TextSerializer is used automatically
app = App("myapp", MyState)

@app.command(display="table", headers=["ID", "Name"])
def list_items(state):
    return [{"ID": 1, "Name": "Item"}]
```

## Custom Display Handlers

```python
# Register custom display type
@app.serializer.register("custom")
def handle_custom(data, meta):
    from replkit2.textkit import box, compose
    return compose(
        box(data["title"], title="Custom"),
        data["content"]
    )

@app.command(display="custom")
def custom_view(state):
    return {"title": "Hello", "content": "World"}
```

## Configuration

```python
from replkit2.textkit import config

# Change global width (affects all displays)
config.width = 100
```

## Philosophy

- ASCII-only output for maximum compatibility
- Bundled with ReplKit2, not a separate package
- Display functions return strings
- Composable and extensible