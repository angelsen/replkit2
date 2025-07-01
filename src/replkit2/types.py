from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandMeta:
    """Metadata for command display and behavior."""

    display: str | None = None
    display_opts: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
