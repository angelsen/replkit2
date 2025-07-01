"""ASCII charts and data visualization."""

from .config import config
from .icons import ICONS


def bar_chart(data: dict[str, float], width: int | None = None, show_values: bool = True) -> str:
    """
    Create a horizontal bar chart.

    Example:
        Python  [##########] 85%
        Java    [#######---] 70%
        Go      [####------] 40%
    """
    width = width or config.width

    if not data:
        return ""

    # Find max value and label length
    max_value = max(data.values()) if data.values() else 1
    max_label = max(len(str(label)) for label in data.keys())

    # Calculate bar width (leave room for label, bar, and value)
    value_width = 4 if show_values else 0  # " 99%"
    bar_width = width - max_label - value_width - 4  # "  [" and "]"
    bar_width = max(bar_width, 10)  # Minimum bar width

    lines = []
    for label, value in data.items():
        # Calculate fill
        percentage = value / max_value if max_value > 0 else 0
        filled = int(bar_width * percentage)
        empty = bar_width - filled

        # Build bar
        bar = ICONS["progress_full"] * filled + ICONS["progress_empty"] * empty

        # Format line
        label_str = str(label).ljust(max_label)
        bar_str = f"{ICONS['progress_left']}{bar}{ICONS['progress_right']}"

        if show_values:
            value_str = f" {int(percentage * 100):2d}%"
            lines.append(f"{label_str}  {bar_str}{value_str}")
        else:
            lines.append(f"{label_str}  {bar_str}")

    return "\n".join(lines)


def progress(
    value: float,
    total: float = 100,
    width: int | None = None,
    label: str = "",
    show_percentage: bool = True,
) -> str:
    """
    Create a progress bar.

    Example:
        Processing: [########--] 80%
    """
    width = width or config.width

    # Calculate percentage
    percentage = min(value / total, 1.0) if total > 0 else 0

    # Calculate bar width
    label_width = len(label) + 2 if label else 0
    percent_width = 5 if show_percentage else 0  # " 100%"
    bar_width = width - label_width - percent_width - 2  # "[]"
    bar_width = max(bar_width, 10)

    # Build bar
    filled = int(bar_width * percentage)
    empty = bar_width - filled
    bar = ICONS["progress_full"] * filled + ICONS["progress_empty"] * empty

    # Build result
    parts = []
    if label:
        parts.append(f"{label}: ")
    parts.append(f"{ICONS['progress_left']}{bar}{ICONS['progress_right']}")
    if show_percentage:
        parts.append(f" {int(percentage * 100):3d}%")

    return "".join(parts)


def sparkline(values: list[float], width: int | None = None, height: int = 1) -> str:
    """
    Create a simple ASCII sparkline chart.

    For height=1, uses: _.-^
    For height>1, uses a mini bar chart
    """
    if not values:
        return ""

    width = width or min(len(values), config.width)

    # Sample values if too many
    if len(values) > width:
        step = len(values) / width
        sampled = []
        for i in range(width):
            idx = int(i * step)
            sampled.append(values[idx])
        values = sampled

    if height == 1:
        # Single line sparkline
        chars = "_.-^"
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val or 1

        result = []
        for v in values:
            normalized = (v - min_val) / range_val
            idx = int(normalized * (len(chars) - 1))
            result.append(chars[idx])

        return "".join(result)
    else:
        # Multi-line chart
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val or 1

        lines = []
        for h in range(height, 0, -1):
            line = []
            threshold = (h - 0.5) / height

            for v in values:
                normalized = (v - min_val) / range_val
                if normalized >= threshold:
                    line.append(ICONS["progress_full"])
                else:
                    line.append(" ")

            lines.append("".join(line))

        return "\n".join(lines)
