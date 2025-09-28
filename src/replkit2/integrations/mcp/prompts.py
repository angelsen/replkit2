"""Prompt registration for MCP integration."""

import inspect
from typing import TYPE_CHECKING

from .wrappers import create_wrapper

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ...app import App


def register_prompts(server: "FastMCP", app: "App"):
    """Register all prompts with server."""
    for key, item in app._mcp_components["prompts"].items():
        _register_single_prompt(server, app, key, item)


def _register_single_prompt(server: "FastMCP", app: "App", key, item):
    """Register a single prompt with optional arg_descriptions."""
    # Extract configuration
    func, meta, config = _extract_config(item, app)

    # Extract function name from key
    func_name = key if isinstance(key, str) else key[0]

    # Create wrapper
    wrapper = create_wrapper(app, func, meta, config)

    # Check if we have argument descriptions
    arg_descriptions = config.get("arg_descriptions", {})
    if arg_descriptions:
        _register_with_descriptions(server, wrapper, func_name, config, arg_descriptions)
    else:
        _register_standard(server, wrapper, func_name, config, func)


def _register_with_descriptions(server: "FastMCP", wrapper, func_name: str, config: dict, arg_descriptions: dict):
    """Register prompt with custom argument descriptions."""
    from fastmcp.prompts.prompt import FunctionPrompt, PromptArgument

    # Create arguments with custom descriptions
    arguments = []
    sig = inspect.signature(wrapper)
    for name, param in sig.parameters.items():
        arguments.append(
            PromptArgument(
                name=name,
                description=arg_descriptions.get(name),
                required=(param.default == inspect.Parameter.empty),
            )
        )

    # Create FunctionPrompt directly
    prompt = FunctionPrompt(
        name=config.get("name", func_name),
        description=config.get("description", wrapper.__doc__),
        arguments=arguments,
        tags=config.get("tags", set()),
        enabled=config.get("enabled", True),
        fn=wrapper,
    )

    # Register the prompt with the server
    server._prompt_manager.add_prompt(prompt)


def _register_standard(server: "FastMCP", wrapper, func_name: str, config: dict, func):
    """Register prompt using FastMCP's auto-detection."""
    server.prompt(
        name=config.get("name", func_name),
        description=config.get("description", func.__doc__),
        tags=config.get("tags"),
        enabled=config.get("enabled", True),
    )(wrapper)


def _extract_config(item, app):
    """Extract func, meta, and config from component item."""
    # Handle both old (func, meta) and new (func, meta, config) formats
    if len(item) == 3:
        func, meta, config = item
    else:
        func, meta = item
        config = meta.fastmcp

    return func, meta, config
