from dataclasses import dataclass, field
from typing import Any, TypedDict, Literal, NotRequired


class FastMCPToolAlias(TypedDict):
    """Alias configuration for MCP tools."""

    name: str
    description: NotRequired[str]
    param_mapping: NotRequired[dict[str, str]]


class FastMCPTool(TypedDict):
    """Configuration for MCP tool registration.

    Fields:
        type: Must be "tool" to register as MCP tool
        tags: Optional tags for categorization/filtering
        description: Optional tool description (overrides function docstring)
        mime_type: MIME type for tool results (e.g., "text/plain", "application/json")
        enabled: Whether tool is enabled (default: True)
        aliases: Alternative names for the tool (str or FastMCPToolAlias with param mapping)
        args: Subset of parameters to expose (default: all non-state/_ctx params)
    """

    type: Literal["tool"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    mime_type: NotRequired[str]
    enabled: NotRequired[bool]
    aliases: NotRequired[list[str | FastMCPToolAlias]]
    args: NotRequired[list[str]]


class FastMCPResource(TypedDict):
    """Configuration for MCP resource registration.

    Fields:
        type: Must be "resource" to register as MCP resource
        uri: URI template with {param} placeholders (e.g., "note://{id}")
        tags: Optional tags for categorization/filtering
        description: Optional resource description (overrides function docstring)
        mime_type: MIME type for resource content (e.g., "text/plain", "application/json")
        enabled: Whether resource is enabled (default: True)
        stub: If True or dict, provides stub() listing without parameters. Dict values are defaults.
        args: Subset of parameters to expose (default: all non-state/_ctx params)
    """

    type: Literal["resource"]
    uri: NotRequired[str]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    mime_type: NotRequired[str]
    enabled: NotRequired[bool]
    stub: NotRequired[bool | dict[str, Any]]
    args: NotRequired[list[str]]


class FastMCPPrompt(TypedDict):
    """Configuration for MCP prompt registration.

    Fields:
        type: Must be "prompt" to register as MCP prompt
        tags: Optional tags for categorization/filtering
        description: Optional prompt description (overrides function docstring)
        enabled: Whether prompt is enabled (default: True)
        arg_descriptions: Human-readable descriptions for each parameter (param_name -> description)
    """

    type: Literal["prompt"]
    tags: NotRequired[set[str]]
    description: NotRequired[str]
    enabled: NotRequired[bool]
    arg_descriptions: NotRequired[dict[str, str]]


class FastMCPDisabled(TypedDict):
    """Type for disabling MCP functionality."""

    enabled: Literal[False]


FastMCPSingleConfig = FastMCPTool | FastMCPResource | FastMCPPrompt | FastMCPDisabled
FastMCPConfig = FastMCPSingleConfig | list[FastMCPSingleConfig]


class FastMCPDefaults(TypedDict, total=False):
    """Default values for MCP configuration fields.

    All fields are optional. Used to set defaults that apply to all commands
    unless overridden in individual command configurations.

    Fields:
        name: Default name override for MCP registration
        description: Default description for MCP commands
        tags: Default tags applied to all MCP commands
        enabled: Default enabled state (default: True)
    """

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
    """Metadata for command configuration.

    Contains all configuration options for commands including display formatting,
    integration settings (MCP, Typer CLI), and data transformation options.

    Fields:
        display: Display type for output formatting ("table", "list", "box", etc.)
        display_opts: Additional options passed to the display formatter (e.g., headers, width)
        aliases: Alternative command names
        fastmcp: MCP integration config (single config or list for multi-registration)
        typer: Typer CLI integration config (or {"enabled": False} to disable)
        truncate: Per-column truncation settings {column_name: {"width": 50, "suffix": "..."}}
        transforms: Per-column transform functions {column_name: "transform_name"}
    """

    display: str | None = None
    display_opts: dict[str, Any] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    fastmcp: FastMCPConfig | None = None  # Can be single config or list of configs
    typer: TyperCLI | None = None
    truncate: dict[str, dict] | None = None  # Per-column truncation config
    transforms: dict[str, str] | None = None  # Per-column transform names
