"""TextFormatter for ReplKit2 integration with Flask-like registration."""

from typing import Any, Callable, override

from ..types.core import CommandMeta
from ..formatters import Formatter

from .display import box, table, list_display, tree
from .charts import bar_chart, progress
from .markdown import format_markdown


class TextFormatter(Formatter):
    """Extensible text formatter with decorator-based handler registration."""

    def __init__(self):
        self._handlers: dict[str, Callable[[Any, CommandMeta, "TextFormatter"], str]] = {}
        self._register_defaults()

    def register(self, display_type: str):
        """Decorator to register a display handler."""

        def decorator(func: Callable[[Any, CommandMeta, "TextFormatter"], str]):
            self._handlers[display_type] = func
            return func

        return decorator

    @override
    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to text using registered handlers."""
        if not meta.display:
            return str(data)

        handler = self._handlers.get(meta.display)
        if handler:
            return handler(data, meta, self)
        # Default: simple string representation
        return str(data)

    def _register_defaults(self):
        """Register built-in display handlers."""

        @self.register("table")
        def handle_table(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            headers = meta.display_opts.get("headers")

            # Handle list of dicts
            if isinstance(data, list) and data and isinstance(data[0], dict):
                if not headers:
                    headers = list(data[0].keys())
                # Case-insensitive header matching: find first key that matches case-insensitively
                rows = [
                    [next((v for k, v in row.items() if k.lower() == h.lower()), "") for h in headers] for row in data
                ]
                return table(rows, headers)

            # Handle list of lists
            elif isinstance(data, list):
                return table(data, headers)

            return str(data)

        @self.register("box")
        def handle_box(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            title = meta.display_opts.get("title")
            width = meta.display_opts.get("width")
            return box(str(data), title, width)

        @self.register("list")
        def handle_list(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            style = meta.display_opts.get("style", "bullet")
            numbered = meta.display_opts.get("numbered", False)

            if isinstance(data, list):
                items = [str(item) for item in data]
                return list_display(items, style, numbered)

            return str(data)

        @self.register("tree")
        def handle_tree(data: Any, _meta: CommandMeta, _formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            if isinstance(data, dict):
                return tree(data)
            return str(data)

        @self.register("bar_chart")
        def handle_bar_chart(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            width = meta.display_opts.get("width")
            show_values = meta.display_opts.get("show_values", True)

            if isinstance(data, dict):
                return bar_chart(data, width, show_values)
            return str(data)

        @self.register("progress")
        def handle_progress(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            width = meta.display_opts.get("width")
            show_percentage = meta.display_opts.get("show_percentage", True)

            if isinstance(data, dict) and "value" in data and "total" in data:
                label = data.get("label", "")
                return progress(data["value"], data["total"], width, label, show_percentage)
            elif isinstance(data, (int, float)):
                return progress(data, width=width, show_percentage=show_percentage)
            return str(data)

        @self.register("markdown")
        def handle_markdown(data: Any, meta: CommandMeta, formatter: "TextFormatter") -> str:  # pyright: ignore[reportUnusedFunction]
            # Pass data through to the markdown formatter
            if isinstance(data, dict):
                return format_markdown(data, meta, formatter)
            # If data is not a dict, wrap it in elements
            return format_markdown({"elements": [{"type": "text", "content": str(data)}]}, meta, formatter)
