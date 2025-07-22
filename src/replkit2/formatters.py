from typing import Protocol, Any
import json

from .types import CommandMeta


class Formatter(Protocol):
    """Protocol for formatting command output."""

    def format(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to string representation."""
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
