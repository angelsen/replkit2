# TextKit2

A minimal ASCII display toolkit for Python.

## Core Concepts

- **Display Components**: Box, Table, Tree - all render to ASCII
- **Composable**: Combine displays with `compose()`
- **Protocol-Based**: Any object can implement the display protocol
- **Zero Dependencies**: Pure Python, works everywhere

## Example

```python
from textkit2 import box, table, tree, compose

# Simple box
print(box("Hello, World!", title="Greeting"))

# Table with data
data = [
    ["Alice", 30, "Engineering"],
    ["Bob", 25, "Design"],
]
print(table(data, headers=["Name", "Age", "Dept"]))

# Compose multiple displays
summary = box("3 users online", title="Status")
details = table(data, headers=["Name", "Age", "Dept"])
print(compose(summary, "\n", details))
```

## ReplKit2 Integration

```python
from textkit2 import TextSerializer

# Use with ReplKit2 for automatic ASCII formatting
app = App("myapp", serializer=TextSerializer())
```

## Philosophy

- ASCII-only output for maximum compatibility
- Minimal API surface
- Display objects are immutable
- Renders to strings, not terminals