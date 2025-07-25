# TextKit Architecture: Low-Level vs High-Level APIs

## Overview

ReplKit2's TextKit provides two levels of APIs for text formatting:

1. **Low-Level TextKit**: Direct display primitives that expect specific data types
2. **High-Level Formatters**: Data transformation + display with automatic type handling

## Low-Level TextKit API

The low-level API provides pure display functions that expect data in specific formats:

```python
from replkit2.textkit import table, box, tree, list_display

# table() expects list[list[Any]] - rows of cells
rows = [["Alice", "30", "NYC"], ["Bob", "25", "LA"]]
print(table(rows, headers=["Name", "Age", "City"]))

# box() expects string content
print(box("Hello World", title="Greeting"))

# tree() expects dict[str, Any] 
data = {"root": {"child1": "value1", "child2": ["a", "b"]}}
print(tree(data))

# list_display() expects list[str]
items = ["First item", "Second item", "Third item"]
print(list_display(items, style="bullet"))
```

## High-Level Formatter API

The high-level API handles data transformation automatically:

```python
from replkit2 import App

app = App("demo")

# Formatter automatically converts list[dict] → list[list] for tables
@app.command(display="table", headers=["Name", "Age", "City"])
def users(state):
    return [
        {"Name": "Alice", "Age": 30, "City": "NYC"},
        {"Name": "Bob", "Age": 25, "City": "LA"}
    ]
```

## Custom Display Handlers

Custom display handlers receive three parameters: `(data, meta, formatter)`. This enables proper composition of high-level and low-level APIs.
```python
@app.formatter.register("dashboard")
def dashboard_display(data, meta, formatter):
    # Option 1: Use formatter for automatic conversion
    session_meta = CommandMeta(
        display="table", 
        display_opts={"headers": ["Session", "Status"]}
    )
    session_table = formatter.format(data["sessions"], session_meta)
    
    # Option 2: Manual conversion + direct textkit
    rows = [[s["Session"], s["Status"]] for s in data["sessions"]]
    session_table = table(rows, headers=["Session", "Status"])
    
    # Both options work - use formatter for convenience, textkit for control
    return box(session_table, title="Active Sessions")
```

## When to Use Each API

### Use Low-Level TextKit When:
- You have data already in the correct format (list[list] for tables)
- You need precise control over formatting
- You're building other display primitives
- Performance is critical (avoids transformation overhead)

### Use High-Level Formatter When:
- You have list[dict] data from databases/APIs
- You want automatic type conversions
- You're building composite displays that reuse other formatters
- You want consistent behavior with built-in commands

## Examples

### Using Formatter for Data Transformation
```python
# Let formatter handle dict→list conversion
meta = CommandMeta(display="table", display_opts={"headers": ["Col1", "Col2"]})
result = formatter.format(data, meta)
```

### Mixing Formatter and TextKit
```python
# Use formatter for complex transformations
table_output = formatter.format(complex_data, table_meta)

# Use textkit for simple wrapping
return box(table_output, title="Results")
```

## Best Practices

1. **Default to formatter** for standard displays (table, list, tree)
2. **Use textkit directly** only when you need specific control
3. **Document data expectations** in custom formatters
4. **Test with both** list[dict] and list[list] inputs
5. **Compose formatters** to avoid reimplementing conversions