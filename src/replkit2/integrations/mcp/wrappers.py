"""Wrapper creation and formatting for MCP components."""

import functools
import inspect
import warnings
from typing import Any, Callable, TYPE_CHECKING

from .parameters import SignatureBuilder
from ...types.context import ExecutionContext, TransportType
from ...utils import accepts_context, inject_context

if TYPE_CHECKING:
    from ...app import App
    from ...types.core import CommandMeta

# Track which commands we've warned about (runtime deprecation warning - once per command)
_runtime_deprecation_warnings: set[str] = set()


def _create_mcp_context(config: dict) -> ExecutionContext:
    """Create ExecutionContext for MCP execution from configuration.

    Args:
        config: MCP configuration dict containing 'type' and optional 'mime_type'

    Returns:
        ExecutionContext configured for MCP mode with STDIO transport

    Example:
        >>> config = {"type": "tool", "mime_type": "text/plain"}
        >>> ctx = _create_mcp_context(config)
        >>> ctx.is_mcp()
        True
        >>> ctx.get_component_type()
        'tool'
    """
    component_type = config.get("type", "tool")
    mime_type = config.get("mime_type")

    return ExecutionContext.for_mcp(
        component_type=component_type,
        mime_type=mime_type,
        transport=TransportType.STDIO,
    )


def create_wrapper(app: "App", func: Callable, meta: "CommandMeta", config: dict) -> Callable:
    """Create wrapper with state injection and formatting."""

    @functools.wraps(func)
    def wrapper(**kwargs):
        # Create execution context for MCP mode
        context = _create_mcp_context(config)
        return call_with_formatting(app, func, kwargs, meta, config, context)

    # Check if args filtering is specified
    if "args" in config and config["args"]:
        # Schema-level filtering: only show allowed args in MCP
        wrapper.__signature__ = SignatureBuilder.with_filtered_args(func, config["args"])  # pyright: ignore[reportAttributeAccessIssue]

        # Filter annotations to match signature
        original_annotations = getattr(func, "__annotations__", {})
        wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k in config["args"]}
    else:
        # No filtering: show all params except state and _ctx (existing behavior)
        wrapper.__signature__ = SignatureBuilder.without_state(func)  # pyright: ignore[reportAttributeAccessIssue]

        # Copy annotations excluding 'state' and '_ctx'
        original_annotations = getattr(func, "__annotations__", {})
        wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k not in ("state", "_ctx")}

    return wrapper


def create_mapped_wrapper(
    app: "App", func: Callable, meta: "CommandMeta", config: dict, param_mapping: dict
) -> Callable:
    """Create wrapper with parameter name mapping for tool aliases."""
    # Get original signature and annotations
    sig = inspect.signature(func)
    original_annotations = getattr(func, "__annotations__", {})

    new_params = []
    new_annotations = {}
    reverse_mapping = {}

    # Build new parameter list with mapped names
    for name, param in sig.parameters.items():
        if name in ("state", "_ctx"):
            continue  # Skip state and _ctx parameters

        if name in param_mapping:
            # Create parameter with mapped name
            mapped_name = param_mapping[name]
            new_param = param.replace(name=mapped_name)
            new_params.append(new_param)
            reverse_mapping[mapped_name] = name

            # Copy type annotation to new parameter name
            if name in original_annotations:
                new_annotations[mapped_name] = original_annotations[name]
        else:
            # Keep original parameter name
            new_params.append(param)
            if name in original_annotations:
                new_annotations[name] = original_annotations[name]

    # Create wrapper that reverses the parameter mapping
    @functools.wraps(func)
    def wrapper(**kwargs):
        # Map parameters back to original names
        original_kwargs = {}
        for key, value in kwargs.items():
            original_key = reverse_mapping.get(key, key)
            original_kwargs[original_key] = value

        # Create execution context for MCP mode
        context = _create_mcp_context(config)

        # Call with original parameter names
        return call_with_formatting(app, func, original_kwargs, meta, config, context)

    # Apply the new signature and annotations
    wrapper.__signature__ = sig.replace(parameters=new_params)  # pyright: ignore[reportAttributeAccessIssue]
    wrapper.__annotations__ = new_annotations

    return wrapper


def create_greedy_wrapper(app: "App", func: Callable, meta: "CommandMeta", config: dict) -> Callable:
    """Create wrapper for resources with greedy parameter pattern."""

    @functools.wraps(func)
    def wrapper(**kwargs):
        # Handle greedy params parameter
        if "params" in kwargs:
            from .parameters import parse_greedy_params

            params_str = kwargs.pop("params", "")
            if params_str:
                parsed = parse_greedy_params(func, params_str)
                kwargs.update(parsed)

        # Filter dash placeholders
        kwargs = {k: v for k, v in kwargs.items() if v != "-"}

        # Create execution context for MCP mode
        context = _create_mcp_context(config)

        return call_with_formatting(app, func, kwargs, meta, config, context)

    # Set proper signature for FastMCP validation
    # Note: Greedy resources always include the 'params' parameter for URI pattern matching
    # Args filtering happens at runtime in call_with_formatting(), not at signature level for greedy wrappers
    wrapper.__signature__ = SignatureBuilder.with_greedy_params(func)  # pyright: ignore[reportAttributeAccessIssue]
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    # Copy annotations excluding 'state', '_ctx' and add 'params'
    original_annotations = getattr(func, "__annotations__", {})
    wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k not in ("state", "_ctx")}
    wrapper.__annotations__["params"] = str  # Add params annotation for greedy matching

    return wrapper


def call_with_formatting(
    app: "App", func: Callable, kwargs: dict, meta: "CommandMeta", config: dict, context: ExecutionContext
) -> Any:
    """Call function with state injection, context injection, and formatting.

    Args:
        app: Application instance
        func: Function to call
        kwargs: Keyword arguments for function
        meta: Command metadata
        config: MCP configuration dict
        context: Execution context to inject if function accepts it

    Returns:
        Function result, potentially formatted

    Note:
        Args filtering happens at schema level in create_wrapper().
        By the time kwargs arrive here, they've already been validated
        by FastMCP against the filtered signature.
    """
    # Filter out None values to let defaults take effect
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    # Inject context if function accepts it
    if accepts_context(func):
        filtered_kwargs = inject_context(filtered_kwargs, context)

    # Call original function with state
    result = func(app.state, **filtered_kwargs)

    # Handle prompt-specific formatting
    component_type = config.get("type")
    if component_type == "prompt":
        return _handle_prompt_result(result, app, meta, context)

    # Apply formatting for text-based MIME types
    mime_type = str(config.get("mime_type") or "")
    if mime_type.startswith("text/") and meta.display and result is not None:
        # Warn about deprecated MIME magic (runtime warning - once per command)
        if not accepts_context(func):
            warning_key = f"{func.__module__}.{func.__name__}"
            if warning_key not in _runtime_deprecation_warnings:
                _runtime_deprecation_warnings.add(warning_key)
                warnings.warn(
                    f"\nCommand '{func.__name__}' is using automatic MIME-based formatting "
                    f"(mime_type='{mime_type}') without ExecutionContext.\n"
                    f"\n"
                    f"This behavior is DEPRECATED and will be removed in v0.14.\n"
                    f"\n"
                    f"Add '_ctx: ExecutionContext = None' parameter to control formatting explicitly:\n"
                    f"\n"
                    f"  from replkit2.types import ExecutionContext\n"
                    f"\n"
                    f"  def {func.__name__}(state, ..., _ctx: ExecutionContext = None):\n"
                    f"      if _ctx and _ctx.get_mime_type() == '{mime_type}':\n"
                    f"          return format_as_text(data)\n"
                    f"      return data\n"
                    f"\n"
                    f"See: docs/migration-0.13.md#deprecation-notice-automatic-mime-formatting",
                    FutureWarning,
                    stacklevel=3,  # Points to wrapper call
                )

        return app.formatter.format(result, meta)

    return result


def _handle_prompt_result(result: Any, app: "App", meta: "CommandMeta", context: ExecutionContext) -> dict:
    """Convert various result formats to MCP prompt messages.

    Handles:
    - Dict with "messages" key containing elements content
    - String (auto-wrapped as user message)
    - Dict with "elements" key (rendered to markdown)
    - Other types (converted to string)

    Args:
        result: Prompt function result
        app: Application instance
        meta: Command metadata
        context: Execution context

    Returns:
        Dict with "messages" key for MCP protocol
    """
    # Already in message format
    if isinstance(result, dict) and "messages" in result:
        processed_messages = []

        for msg in result["messages"]:
            content = msg.get("content", {})

            # Handle our extension: elements content type
            if isinstance(content, dict) and content.get("type") == "elements":
                # Render elements to markdown using existing formatter
                elements_dict = {"elements": content.get("elements", [])}
                markdown_text = app.formatter.format(elements_dict, meta) if meta.display else str(elements_dict)

                processed_messages.append(
                    {"role": msg.get("role", "user"), "content": {"type": "text", "text": markdown_text}}
                )
            else:
                # Standard content - pass through as-is
                processed_messages.append(msg)

        return {"messages": processed_messages}

    # String - wrap as user message
    if isinstance(result, str):
        return {"messages": [{"role": "user", "content": {"type": "text", "text": result}}]}

    # Dict with elements - render and wrap as user message
    if isinstance(result, dict) and "elements" in result:
        markdown_text = app.formatter.format(result, meta) if meta.display else str(result)
        return {"messages": [{"role": "user", "content": {"type": "text", "text": markdown_text}}]}

    # Fallback - convert to string and wrap
    return {"messages": [{"role": "user", "content": {"type": "text", "text": str(result)}}]}
