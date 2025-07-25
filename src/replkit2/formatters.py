from typing import Protocol, Any, Callable
import json

from .types.core import CommandMeta


class Formatter(Protocol):
    """Protocol for formatting command output."""

    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to string representation."""
        ...


class ExtensibleFormatter(Formatter, Protocol):
    """Protocol for formatters that support handler registration."""

    def register(
        self, display_type: str
    ) -> Callable[
        [Callable[[Any, CommandMeta, "ExtensibleFormatter"], str]],
        Callable[[Any, CommandMeta, "ExtensibleFormatter"], str],
    ]:
        """Register a display handler."""
        ...


class JSONFormatter:
    """Format command output as JSON."""

    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to JSON string."""
        return json.dumps(data, indent=2)


class PassthroughFormatter:
    """Return data unchanged - useful for API endpoints."""

    def format(self, data: Any, meta: CommandMeta) -> Any:
        """Return data as-is without transformation."""
        return data
