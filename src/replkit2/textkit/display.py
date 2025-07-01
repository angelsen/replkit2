"""Display components for structured data."""

from typing import Any
from .config import config
from .core import wrap
from .icons import ICONS


def table(rows: list[list[Any]], headers: list[str] | None = None) -> str:
    """
    Format data as an ASCII table.

    Example:
        name    age  city
        ------  ---  --------
        Alice   30   New York
        Bob     25   London
    """
    if not rows:
        return ""

    # Convert all values to strings
    str_rows = [[str(cell) for cell in row] for row in rows]

    # Calculate column widths
    if headers:
        num_cols = len(headers)
        col_widths = [len(h) for h in headers]
        # Ensure all rows have same number of columns
        str_rows = [row[:num_cols] + [""] * (num_cols - len(row)) for row in str_rows]
    else:
        num_cols = max(len(row) for row in str_rows) if str_rows else 0
        col_widths = [0] * num_cols

    # Update widths based on data
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    # Build table
    result: list[str] = []

    # Headers
    if headers:
        header_row: list[str] = []
        separator_row: list[str] = []
        for i, header in enumerate(headers):
            header_row.append(header.ljust(col_widths[i]))
            separator_row.append("-" * col_widths[i])
        result.append("  ".join(header_row))
        result.append("  ".join(separator_row))

    # Data rows
    for row in str_rows:
        formatted_row: list[str] = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                formatted_row.append(cell.ljust(col_widths[i]))
        result.append("  ".join(formatted_row))

    return "\n".join(result)


def box(content: str, title: str | None = None, width: int | None = None) -> str:
    """
    Draw a box around content with optional title.

    Example:
        +-- Title -------+
        | Content line 1 |
        | Content line 2 |
        +----------------+
    """
    width = width or config.width
    lines = content.strip().split("\n")

    # Calculate inner width (accounting for borders and padding)
    inner_width = width - 4  # "| " and " |"

    # Wrap lines if needed
    wrapped_lines: list[str] = []
    for line in lines:
        if len(line) > inner_width:
            wrapped_lines.extend(wrap(line, inner_width))
        else:
            wrapped_lines.append(line)

    # Use the full width if specified, otherwise fit to content
    if width and width > 0:
        box_width = width
        inner_width = box_width - 4
    else:
        # Find actual max width
        max_line_width = (
            max(len(line) for line in wrapped_lines) if wrapped_lines else 0
        )
        if title:
            max_line_width = max(max_line_width, len(title) + 2)
        box_width = max_line_width + 4
        inner_width = box_width - 4

    # Build box
    result: list[str] = []

    # Top border
    if title:
        title_str = f" {title} "
        padding = inner_width - len(title) - 2
        left_pad = 2
        right_pad = padding - left_pad + 2
        result.append(f"+{'-' * left_pad}{title_str}{'-' * right_pad}+")
    else:
        result.append(f"+{'-' * (box_width - 2)}+")

    # Content lines
    for line in wrapped_lines:
        padding = inner_width - len(line)
        result.append(f"| {line}{' ' * padding} |")

    # Bottom border
    result.append(f"+{'-' * (box_width - 2)}+")

    return "\n".join(result)


def list_display(
    items: list[str], style: str = "bullet", numbered: bool = False
) -> str:
    """
    Format items as a list.

    Styles: 'bullet', 'arrow', 'dash', 'check', 'uncheck'
    """
    if not items:
        return ""

    if numbered:
        width = len(str(len(items)))
        return "\n".join(f"{i + 1:>{width}}. {item}" for i, item in enumerate(items))
    else:
        prefix = ICONS.get(style, ICONS["bullet"])
        return "\n".join(f"{prefix}{item}" for item in items)


def tree(data: dict[str, Any], _prefix: str = "") -> str:
    """
    Format hierarchical data as a tree.

    Example:
        root
        |-- child1
        |   |-- grandchild1
        |   `-- grandchild2
        `-- child2
    """
    lines: list[str] = []
    items = list(data.items())

    for i, (key, value) in enumerate(items):
        is_last = i == len(items) - 1

        # Current item
        if _prefix:
            if is_last:
                lines.append(_prefix + ICONS["tree_last"] + str(key))
                new_prefix = _prefix + ICONS["tree_space"]
            else:
                lines.append(_prefix + ICONS["tree_branch"] + str(key))
                new_prefix = _prefix + ICONS["tree_pipe"]
        else:
            lines.append(str(key))
            # For root level, add appropriate prefix for children
            if is_last:
                new_prefix = ICONS["tree_space"]
            else:
                new_prefix = ICONS["tree_pipe"]

        # Handle different value types
        if isinstance(value, dict):
            # Extend with the lines from the nested tree
            subtree = tree(value, new_prefix)
            if subtree:
                lines.extend(subtree.split("\n"))
        elif isinstance(value, list):
            for j, item in enumerate(value):
                is_last_item = j == len(value) - 1
                if is_last_item:
                    lines.append(new_prefix + ICONS["tree_last"] + str(item))
                else:
                    lines.append(new_prefix + ICONS["tree_branch"] + str(item))
        else:
            # Display simple values inline with the key
            lines[-1] = lines[-1] + ": " + str(value)

    return "\n".join(lines)
