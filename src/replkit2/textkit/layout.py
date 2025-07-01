"""Layout and composition utilities."""

from .config import config


def hr(char: str | None = None, width: int | None = None) -> str:
    """Create a horizontal rule."""
    char = char or config.hr_char
    width = width or config.width
    return char * width


def columns(items: list[str], cols: int = 2, gap: int = 2, width: int | None = None) -> str:
    """
    Arrange items in columns.

    Example:
        Item 1    Item 4
        Item 2    Item 5
        Item 3    Item 6
    """
    width = width or config.width

    if not items or cols < 1:
        return ""

    # Calculate column width
    col_width = (width - gap * (cols - 1)) // cols

    # Split items into columns
    rows_count = (len(items) + cols - 1) // cols

    lines = []
    for row in range(rows_count):
        row_items = []
        for col in range(cols):
            idx = row + col * rows_count
            if idx < len(items):
                # Truncate or pad item to fit column
                item = items[idx][:col_width].ljust(col_width)
                row_items.append(item)
            else:
                row_items.append(" " * col_width)

        lines.append((" " * gap).join(row_items).rstrip())

    return "\n".join(lines)


def grid(items: list[list[str]], gap: int = 2, width: int | None = None) -> str:
    """
    Create a grid layout from a 2D list.

    Example:
        A1  B1  C1
        A2  B2  C2
        A3  B3  C3
    """
    width = width or config.width

    if not items:
        return ""

    # Find max columns
    max_cols = max(len(row) for row in items)

    # Calculate column widths
    col_widths = [0] * max_cols
    for row in items:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # Adjust widths to fit
    total_width = sum(col_widths) + gap * (max_cols - 1)
    if total_width > width:
        # Scale down proportionally
        scale = width / total_width
        col_widths = [int(w * scale) for w in col_widths]

    # Build grid
    lines = []
    for row in items:
        cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cells.append(cell[: col_widths[i]].ljust(col_widths[i]))

        lines.append((" " * gap).join(cells).rstrip())

    return "\n".join(lines)


def compose(*elements: str, sep: str = "\n", spacing: int | None = None) -> str:
    """
    Compose multiple display elements together with configurable spacing.

    Args:
        *elements: Display elements to compose
        sep: Separator string (default: newline)
        spacing: Number of blank lines between components (default: from config)

    Example:
        compose(
            box("Status: OK"),
            hr(),
            table(data),
            spacing=2  # Add 2 blank lines between each component
        )
    """
    if spacing is None:
        spacing = config.component_spacing

    # Create the actual separator with spacing
    separator = sep * (spacing + 1) if spacing > 0 else sep

    return separator.join(str(e) for e in elements if e)
