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
    stub: NotRequired[bool | dict[str, Any]]


class FastMCPPrompt(TypedDict):
    type: Literal["prompt"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    enabled: NotRequired[bool]


class FastMCPDisabled(TypedDict):
    """Type for disabling MCP functionality."""

    enabled: Literal[False]


FastMCPConfig = FastMCPTool | FastMCPResource | FastMCPPrompt | FastMCPDisabled


class FastMCPDefaults(TypedDict, total=False):
    name: str
    description: str
    tags: set[str]
    enabled: bool


class TyperConfig(TypedDict):
    """Configuration for Typer CLI integration."""

    enabled: NotRequired[bool]
    name: NotRequired[str]
    help: NotRequired[str]
    epilog: NotRequired[str]
    short_help: NotRequired[str]
    hidden: NotRequired[bool]
    rich_help_panel: NotRequired[str]


class TyperDisabled(TypedDict):
    """Exclude command from CLI."""

    enabled: Literal[False]


TyperCLI = TyperConfig | TyperDisabled


@dataclass
class CommandMeta:
    display: str | None = None
    display_opts: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    fastmcp: FastMCPConfig | None = None
    typer: TyperCLI | None = None
