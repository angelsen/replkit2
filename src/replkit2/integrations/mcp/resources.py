"""Resource registration for MCP integration."""

from typing import TYPE_CHECKING, Callable

from .parameters import ParameterAnalyzer, parse_greedy_params
from .uri import URIBuilder
from .wrappers import create_wrapper, create_greedy_wrapper, call_with_formatting

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ...app import App
    from ...types.core import CommandMeta


def register_resources(server: "FastMCP", app: "App"):
    """Register all resources with appropriate strategies."""
    analyzer = ParameterAnalyzer()
    uri_builder = URIBuilder(app.uri_scheme)

    for key, item in app._mcp_components["resources"].items():
        _register_single_resource(server, app, key, item, analyzer, uri_builder)


def _register_single_resource(
    server: "FastMCP", app: "App", key, item, analyzer: ParameterAnalyzer, uri_builder: URIBuilder
):
    """Select and apply appropriate registration strategy."""
    # Extract configuration
    func, meta, config = _extract_config(item, app)

    # Validate resource parameters follow URI constraints
    from ...validation import validate_mcp_resource_params

    # Check for explicit args override
    if "args" in config and not config.get("args"):
        # Empty args list - force no parameters
        _register_simple(server, app, func, meta, config, uri_builder)
        return

    # Validate parameters
    validate_mcp_resource_params(func)

    # Strategy selection
    if analyzer.is_all_optional(func):
        # All-optional: dual registration (base + template)
        _register_all_optional(server, app, func, meta, config, uri_builder)
    elif analyzer.has_optional_parameters(func):
        # Mixed: single registration with greedy pattern
        _register_greedy(server, app, func, meta, config, uri_builder, analyzer)
    else:
        # Simple: direct registration
        _register_simple(server, app, func, meta, config, uri_builder)


def _register_simple(
    server: "FastMCP", app: "App", func: Callable, meta: "CommandMeta", config: dict, uri_builder: URIBuilder
):
    """Register simple resource with direct parameter mapping."""
    # Handle explicit empty args
    if "args" in config and not config["args"]:
        uri = f"{app.uri_scheme}://{func.__name__}"
    else:
        uri = config.get("uri") or uri_builder.build_simple(func)

    # Create wrapper
    wrapper = create_wrapper(app, func, meta, config)

    # Register resource
    server.resource(
        uri=uri,
        name=config.get("name", func.__name__),
        description=config.get("description", func.__doc__),
        mime_type=config.get("mime_type"),
        tags=config.get("tags"),
        enabled=config.get("enabled", True),
    )(wrapper)


def _register_greedy(
    server: "FastMCP",
    app: "App",
    func: Callable,
    meta: "CommandMeta",
    config: dict,
    uri_builder: URIBuilder,
    analyzer: ParameterAnalyzer,
):
    """Register resource with greedy pattern for optional parameters."""
    uri = config.get("uri") or uri_builder.build_greedy(func)

    # Create wrapper with greedy params support
    wrapper = create_greedy_wrapper(app, func, meta, config)

    # Register resource
    server.resource(
        uri=uri,
        name=config.get("name", func.__name__),
        description=config.get("description", func.__doc__),
        mime_type=config.get("mime_type"),
        tags=config.get("tags"),
        enabled=config.get("enabled", True),
    )(wrapper)

    # Register stub if requested
    stub_config = config.get("stub")
    if stub_config:
        _register_stub(server, func, uri, stub_config, uri_builder)


def _register_all_optional(
    server: "FastMCP", app: "App", func: Callable, meta: "CommandMeta", config: dict, uri_builder: URIBuilder
):
    """Dual registration for all-optional functions."""
    base_uri = f"{app.uri_scheme}://{func.__name__}"
    name = func.__name__

    # 1. Base Resource (no parameters - all defaults)
    def base_wrapper():
        return call_with_formatting(app, func, {}, meta, config)

    base_wrapper.__name__ = f"{name}_base"
    base_wrapper.__doc__ = f"{func.__doc__} (with all defaults)"

    server.resource(
        uri=base_uri,
        name=config.get("name", name),
        description=config.get("description", func.__doc__),
        mime_type=config.get("mime_type"),
        tags=config.get("tags"),
        enabled=config.get("enabled", True),
    )(base_wrapper)

    # 2. Template Resource (with greedy parameters)
    template_uri = f"{base_uri}/{{params*}}"

    def template_wrapper(params: str = ""):
        kwargs = parse_greedy_params(func, params)
        return call_with_formatting(app, func, kwargs, meta, config)

    template_wrapper.__name__ = f"{name}_template"
    template_wrapper.__doc__ = f"{func.__doc__} (with parameters)"

    server.resource(
        uri=template_uri,
        name=f"{config.get('name', name)}_with_params",
        description=config.get("description", func.__doc__),
        mime_type=config.get("mime_type"),
        tags=config.get("tags"),
        enabled=config.get("enabled", True),
    )(template_wrapper)

    # Register stub for template if requested
    stub_config = config.get("stub")
    if stub_config:
        _register_stub(server, func, template_uri, stub_config, uri_builder)


def _register_stub(server: "FastMCP", func: Callable, uri_template: str, stub_config, uri_builder: URIBuilder):
    """Register stub resource for examples."""
    # Generate stub URI with enhanced notation
    stub_uri = uri_builder.build_stub(func, uri_template)

    # Get response data
    if isinstance(stub_config, dict) and "response" in stub_config:
        response_data = stub_config["response"]
    else:
        response_data = {
            "description": func.__doc__.strip().split("\n")[0] if func.__doc__ else f"Usage for {uri_template}",
            "template": uri_template,
        }

    # Create and register stub function
    def stub_func():
        return response_data

    stub_func.__name__ = f"{func.__name__}_stub"
    stub_func.__doc__ = f"Example usage for {uri_template}"

    server.resource(
        uri=stub_uri,
        name=f"{func.__name__}_example",
        description=f"Example usage for {func.__name__}",
    )(stub_func)


def _extract_config(item, app):
    """Extract func, meta, and config from component item."""
    # Handle both old (func, meta) and new (func, meta, config) formats
    if len(item) == 3:
        func, meta, config = item
    else:
        func, meta = item
        config = meta.fastmcp

    return func, meta, config
