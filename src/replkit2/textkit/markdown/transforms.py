"""Common data transformations for markdown elements."""

from typing import Any, Callable
from datetime import datetime


def format_size(value: Any) -> str:
    """Format bytes as human readable size.

    Args:
        value: Byte count (int, str, or None)

    Returns:
        Human readable size string (e.g., "1.5M", "23K", "456B")
    """
    if not value:
        return "-"

    try:
        bytes_val = int(value)
        if bytes_val < 0:
            return "-"
        elif bytes_val < 1024:
            return f"{bytes_val}B"
        elif bytes_val < 1024**2:
            return f"{bytes_val / 1024:.1f}K"
        elif bytes_val < 1024**3:
            return f"{bytes_val / 1024**2:.1f}M"
        else:
            return f"{bytes_val / 1024**3:.1f}G"
    except (ValueError, TypeError):
        return "-"


def format_timestamp(value: Any) -> str:
    """Format millisecond timestamp as readable time.

    Args:
        value: Millisecond timestamp (float, int, str, or None)

    Returns:
        Formatted time string (HH:MM:SS)
    """
    if not value:
        return "-"

    try:
        ms = float(value)
        dt = datetime.fromtimestamp(ms / 1000)
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError, OSError):
        return "-"


def format_number(value: Any) -> str:
    """Format number with thousand separators.

    Args:
        value: Number to format

    Returns:
        Formatted number string with commas
    """
    if value is None or value == "":
        return "-"

    try:
        num = float(value)
        if num == int(num):
            return f"{int(num):,}"
        else:
            return f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_duration(value: Any) -> str:
    """Format seconds as human readable duration.

    Args:
        value: Duration in seconds

    Returns:
        Human readable duration (e.g., "2h 15m", "45s", "3d 2h")
    """
    if not value:
        return "-"

    try:
        seconds = int(value)
        if seconds < 0:
            return "-"

        # Calculate components
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        # Build string
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")

        # Return first two components for readability
        return " ".join(parts[:2])
    except (ValueError, TypeError):
        return "-"


def format_percentage(value: Any) -> str:
    """Format decimal as percentage.

    Args:
        value: Decimal value (0.0 to 1.0)

    Returns:
        Percentage string (e.g., "45.2%")
    """
    if value is None or value == "":
        return "-"

    try:
        num = float(value)
        return f"{num * 100:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def format_boolean(value: Any) -> str:
    """Format boolean as check mark or X.

    Args:
        value: Boolean value

    Returns:
        "[x]" for True, "[ ]" for False
    """
    if value is None:
        return "[ ]"

    # Handle string booleans
    if isinstance(value, str):
        value = value.lower() in ("true", "yes", "1", "on")

    return "[x]" if value else "[ ]"


# Registry of all available transforms
TRANSFORMS: dict[str, Callable[[Any], str]] = {
    "format_size": format_size,
    "format_timestamp": format_timestamp,
    "format_number": format_number,
    "format_duration": format_duration,
    "format_percentage": format_percentage,
    "format_boolean": format_boolean,
    # Aliases for convenience
    "size": format_size,
    "timestamp": format_timestamp,
    "number": format_number,
    "duration": format_duration,
    "percentage": format_percentage,
    "boolean": format_boolean,
    "bool": format_boolean,
}


def apply_transform(value: Any, transform_name: str) -> str:
    """Apply a named transform to a value.

    Args:
        value: Value to transform
        transform_name: Name of transform to apply

    Returns:
        Transformed string value, or original value as string if transform not found
    """
    if transform_name in TRANSFORMS:
        return TRANSFORMS[transform_name](value)
    return str(value)


def register_transform(name: str, func: Callable[[Any], str]):
    """Register a custom transform function.

    Args:
        name: Name to register the transform under
        func: Transform function that takes Any and returns str
    """
    TRANSFORMS[name] = func
