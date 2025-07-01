from typing import Protocol, Any
import json

from .types import CommandMeta


class Serializer(Protocol):
    """Protocol for serializing command output."""

    def serialize(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to string representation."""
        ...


class JSONSerializer:
    """Serialize command output as JSON."""

    def serialize(self, data: Any, meta: CommandMeta) -> str:
        """Convert data to JSON string."""
        return json.dumps(data, indent=2)


class PassthroughSerializer:
    """Return data unchanged - useful for API endpoints."""

    def serialize(self, data: Any, meta: CommandMeta) -> Any:
        """Return data as-is without transformation."""
        return data
