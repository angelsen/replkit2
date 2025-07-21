"""Display components for structured data."""

from typing import Any
from .config import config
from .core import wrap
from .icons import ICONS


def table(
    rows: list[list[Any]],
    headers: list[str] | None = None,
    width: int | None = None,
    col_widths: list[int] | None = None,
    wrap_cells: bool = False,
) -> str:
    """
    Format data as an ASCII table.

    Args:
        rows: Table data rows
        headers: Optional column headers
        width: Total table width (distributes proportionally)
        col_widths: Specific column widths (overrides auto-sizing)
        wrap_cells: Whether to wrap long cell content across multiple lines

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

    # Determine number of columns
    if headers:
        num_cols = len(headers)
        # Ensure all rows have same number of columns
        str_rows = [row[:num_cols] + [""] * (num_cols - len(row)) for row in str_rows]
    else:
        num_cols = max(len(row) for row in str_rows) if str_rows else 0

    # Calculate column widths
    if col_widths:
        # Use provided column widths
        if len(col_widths) < num_cols:
            # Pad with auto-sized columns
            col_widths = list(col_widths) + [0] * (num_cols - len(col_widths))
    else:
        # Auto-size columns
        col_widths = [0] * num_cols

        # Start with header widths if available
        if headers:
            for i, header in enumerate(headers):
                if i < len(col_widths):
                    col_widths[i] = len(header)

        # Update widths based on data
        for row in str_rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))

    # Apply total width constraint if specified
    if width:
        # Calculate gaps between columns
        gap_width = 2 * (num_cols - 1)  # "  " between columns
        available_width = width - gap_width

        # If col_widths were provided, respect them but scale if needed
        current_total = sum(col_widths)

        if current_total > available_width:
            # Scale down proportionally
            scale = available_width / current_total
            col_widths = [max(1, int(w * scale)) for w in col_widths]
        elif current_total < available_width:
            # Distribute extra space proportionally
            extra = available_width - current_total
            if current_total > 0:
                # Distribute based on current proportions
                for i in range(num_cols):
                    col_widths[i] += int(col_widths[i] * extra / current_total)
            else:
                # Equal distribution
                for i in range(num_cols):
                    col_widths[i] += extra // num_cols
                # Add remainder to last column
                if num_cols > 0:
                    col_widths[-1] += extra % num_cols

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
        if wrap_cells:
            # Wrap each cell and handle multi-line rows
            wrapped_cells = []
            max_lines = 1

            for i, cell in enumerate(row):
                if i < len(col_widths):
                    # Wrap the cell content
                    if len(cell) > col_widths[i]:
                        wrapped = wrap(cell, col_widths[i])
                        wrapped_cells.append(wrapped)
                        max_lines = max(max_lines, len(wrapped))
                    else:
                        wrapped_cells.append([cell])
                else:
                    wrapped_cells.append([""])

            # Output each line of the multi-line row
            for line_idx in range(max_lines):
                formatted_row: list[str] = []
                for i, cell_lines in enumerate(wrapped_cells):
                    if i < len(col_widths):
                        # Get the line for this cell, or empty if no more lines
                        line = cell_lines[line_idx] if line_idx < len(cell_lines) else ""
                        formatted_row.append(line.ljust(col_widths[i]))
                result.append("  ".join(formatted_row))
        else:
            # Simple truncation (existing behavior)
            simple_row: list[str] = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    # Truncate if too long
                    if len(cell) > col_widths[i]:
                        truncated = cell[: col_widths[i] - 3] + "..."
                        simple_row.append(truncated)
                    else:
                        simple_row.append(cell.ljust(col_widths[i]))
            result.append("  ".join(simple_row))

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
        max_line_width = max(len(line) for line in wrapped_lines) if wrapped_lines else 0
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


def list_display(items: list[str], style: str = "bullet", numbered: bool = False) -> str:
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
