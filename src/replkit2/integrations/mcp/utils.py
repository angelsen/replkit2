"""Shared utilities for MCP integration."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ...app import App
    from ...types.core import CommandMeta


def extract_config(item: tuple, app: "App") -> tuple[Callable, "CommandMeta", dict]:
    """Extract func, meta, and config from component item.

    Args:
        item: Component tuple from app._mcp_components (2 or 3 elements)
        app: App instance (unused but kept for API compatibility)

    Returns:
        Tuple of (function, CommandMeta, config_dict)

    The function handles both old (func, meta) and new (func, meta, config) formats.
    For old format, extracts config from meta.fastmcp.
    """
    # Handle both old (func, meta) and new (func, meta, config) formats
    if len(item) == 3:
        func, meta, config = item
    else:
        func, meta = item
        config = meta.fastmcp

    return func, meta, config
