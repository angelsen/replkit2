"""TextKit - ASCII display toolkit for ReplKit2."""

# Config
from .config import config

# Core utilities
from .core import truncate, align, wrap, indent

# Display components
from .display import table, box, list_display, tree

# Charts
from .charts import bar_chart, progress, sparkline

# Layout
from .layout import hr, columns, grid, compose

# Icons
from .icons import ICONS

# Formatter for ReplKit2
from .formatter import TextFormatter

# Markdown
from .markdown import markdown, MarkdownElement

__all__ = [
    # Config
    "config",
    # Core
    "truncate",
    "align",
    "wrap",
    "indent",
    # Display
    "table",
    "box",
    "list_display",
    "tree",
    # Charts
    "bar_chart",
    "progress",
    "sparkline",
    # Layout
    "hr",
    "columns",
    "grid",
    "compose",
    # Icons
    "ICONS",
    # Formatter
    "TextFormatter",
    # Markdown
    "markdown",
    "MarkdownElement",
]
