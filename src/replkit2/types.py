from dataclasses import dataclass, field
from typing import Any, TypedDict, Literal, NotRequired


class FastMCPTool(TypedDict):
    type: Literal["tool"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    enabled: NotRequired[bool]


class FastMCPResource(TypedDict):
    type: Literal["resource"]
    uri: NotRequired[str]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    mime_type: NotRequired[str]
    enabled: NotRequired[bool]


class FastMCPPrompt(TypedDict):
    type: Literal["prompt"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    enabled: NotRequired[bool]


FastMCPConfig = FastMCPTool | FastMCPResource | FastMCPPrompt


class FastMCPDefaults(TypedDict, total=False):
    tags: set[str]
    enabled: bool


@dataclass
class CommandMeta:
    display: str | None = None
    display_opts: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    fastmcp: FastMCPConfig | None = None
