from typing import Protocol, Any, Callable
import json

from .types.core import CommandMeta


class Formatter(Protocol):
    """Protocol for formatting command output.

    Formatters are pure presentation layer - they receive data and metadata
    to produce formatted output. Commands handle context-aware logic (data
    selection, behavior), while formatters handle declarative presentation.
    """

    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to string representation.

        Args:
            data: Data to format
            meta: Command metadata with display configuration

        Returns:
            Formatted string representation
        """
        ...


class ExtensibleFormatter(Formatter, Protocol):
    """Protocol for formatters that support handler registration.

    Handlers receive data, metadata, and formatter instance.
    """

    def register(
        self, display_type: str
    ) -> Callable[
        [Callable[[Any, CommandMeta, "ExtensibleFormatter"], str]],
        Callable[[Any, CommandMeta, "ExtensibleFormatter"], str],
    ]:
        """Register a display handler.

        Args:
            display_type: Display type identifier (e.g., "table", "markdown")

        Returns:
            Decorator for registering handler functions
        """
        ...


class JSONFormatter:
    """Format command output as JSON."""

    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to format
            meta: Command metadata

        Returns:
            JSON string representation
        """
        return json.dumps(data, indent=2)


class PassthroughFormatter:
    """Return data unchanged - useful for API endpoints."""

    def format(self, data: Any, meta: CommandMeta) -> Any:
        """Return data as-is without transformation.

        Args:
            data: Data to return
            meta: Command metadata

        Returns:
            Data unchanged
        """
        return data
