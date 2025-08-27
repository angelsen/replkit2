from dataclasses import dataclass, field
from typing import Any, TypedDict, Literal, NotRequired


class FastMCPToolAlias(TypedDict):
    """Alias configuration for MCP tools."""

    name: str
    description: NotRequired[str]
    param_mapping: NotRequired[dict[str, str]]


class FastMCPTool(TypedDict):
    type: Literal["tool"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    mime_type: NotRequired[str]
    enabled: NotRequired[bool]
    aliases: NotRequired[list[str | FastMCPToolAlias]]
    args: NotRequired[list[str]]


class FastMCPResource(TypedDict):
    type: Literal["resource"]
    uri: NotRequired[str]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    mime_type: NotRequired[str]
    enabled: NotRequired[bool]
    stub: NotRequired[bool | dict[str, Any]]
    args: NotRequired[list[str]]


class FastMCPPrompt(TypedDict):
    type: Literal["prompt"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    enabled: NotRequired[bool]


class FastMCPDisabled(TypedDict):
    """Type for disabling MCP functionality."""

    enabled: Literal[False]


FastMCPSingleConfig = FastMCPTool | FastMCPResource | FastMCPPrompt | FastMCPDisabled
FastMCPConfig = FastMCPSingleConfig | list[FastMCPSingleConfig]


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
    fastmcp: FastMCPConfig | None = None  # Can be single config or list of configs
    typer: TyperCLI | None = None
