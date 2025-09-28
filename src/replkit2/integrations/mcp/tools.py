"""Tool registration for MCP integration."""

from typing import TYPE_CHECKING

from .wrappers import create_wrapper, create_mapped_wrapper

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ...app import App


def register_tools(server: "FastMCP", app: "App"):
    """Register all tools with server."""
    for key, item in app._mcp_components["tools"].items():
        _register_single_tool(server, app, key, item)


def _register_single_tool(server: "FastMCP", app: "App", key, item):
    """Register a single tool with aliases."""
    # Extract configuration
    func, meta, config = _extract_config(item, app)

    # Extract function name from key (might be tuple)
    func_name = key if isinstance(key, str) else key[0]

    # Create wrapper
    wrapper = create_wrapper(app, func, meta, config)

    # Prepare registration kwargs
    tool_kwargs = {
        "name": config.get("name", func_name),
        "description": config.get("description", func.__doc__),
        "tags": config.get("tags"),
        "enabled": config.get("enabled", True),
    }

    # Check if this tool uses MIME formatting
    mime_type = str(config.get("mime_type") or "")
    if mime_type.startswith("text/") and meta.display:
        # Disable output schema to prevent structured_content validation of formatted strings
        tool_kwargs["output_schema"] = None

    # Register the tool
    server.tool(**tool_kwargs)(wrapper)

    # Register aliases if specified
    aliases = config.get("aliases", [])
    for alias in aliases:
        _register_tool_alias(server, app, func, meta, config, alias)


def _register_tool_alias(server: "FastMCP", app: "App", func, meta, config, alias):
    """Register tool alias with optional parameter mapping."""
    # Parse alias configuration
    if isinstance(alias, str):
        # Simple string alias - use primary tool's description
        alias_name = alias
        alias_desc = config.get("description", func.__doc__)
        param_mapping = None
    elif isinstance(alias, dict):
        # Advanced alias with custom options
        alias_name = alias.get("name")
        if not alias_name:
            return  # Skip invalid alias
        alias_desc = alias.get("description", config.get("description", func.__doc__))
        param_mapping = alias.get("param_mapping", None)
    else:
        return  # Skip invalid alias format

    # Create wrapper with parameter mapping if needed
    if param_mapping:
        wrapper = create_mapped_wrapper(app, func, meta, config, param_mapping)
    else:
        # Use standard wrapper
        wrapper = create_wrapper(app, func, meta, config)

    # Override the function name for the alias
    wrapper.__name__ = alias_name

    # Prepare tool registration kwargs
    tool_kwargs = {
        "name": alias_name,
        "description": alias_desc,
        "tags": config.get("tags"),
        "enabled": config.get("enabled", True),
    }

    # Check if this tool uses MIME formatting
    mime_type = str(config.get("mime_type") or "")
    if mime_type.startswith("text/") and meta.display:
        tool_kwargs["output_schema"] = None

    # Register the alias
    server.tool(**tool_kwargs)(wrapper)


def _extract_config(item, app):
    """Extract func, meta, and config from component item."""
    # Handle both old (func, meta) and new (func, meta, config) formats
    if len(item) == 3:
        func, meta, config = item
    else:
        func, meta = item
        config = meta.fastmcp

    return func, meta, config
