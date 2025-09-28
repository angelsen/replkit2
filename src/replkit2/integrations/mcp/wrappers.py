"""Wrapper creation and formatting for MCP components."""

import functools
import inspect
from typing import Any, Callable, TYPE_CHECKING

from .parameters import SignatureBuilder

if TYPE_CHECKING:
    from ...app import App
    from ...types.core import CommandMeta


def create_wrapper(app: "App", func: Callable, meta: "CommandMeta", config: dict) -> Callable:
    """Create wrapper with state injection and formatting."""

    @functools.wraps(func)
    def wrapper(**kwargs):
        return call_with_formatting(app, func, kwargs, meta, config)

    # Create signature without state parameter
    wrapper.__signature__ = SignatureBuilder.without_state(func)  # pyright: ignore[reportAttributeAccessIssue]

    # Copy annotations excluding 'state'
    original_annotations = getattr(func, "__annotations__", {})
    wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k != "state"}

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
        if name == "state":
            continue  # Skip state parameter

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

        # Call with original parameter names
        return call_with_formatting(app, func, original_kwargs, meta, config)

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

        return call_with_formatting(app, func, kwargs, meta, config)

    # Set proper signature for FastMCP validation
    wrapper.__signature__ = SignatureBuilder.with_greedy_params(func)  # pyright: ignore[reportAttributeAccessIssue]
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    # Copy annotations excluding 'state' and add 'params'
    original_annotations = getattr(func, "__annotations__", {})
    wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k != "state"}
    wrapper.__annotations__["params"] = str  # Add params annotation for greedy matching

    return wrapper


def call_with_formatting(app: "App", func: Callable, kwargs: dict, meta: "CommandMeta", config: dict) -> Any:
    """Call function with state injection and apply formatting if needed."""
    # Filter to allowed args if specified
    if "args" in config:
        allowed_args = config["args"]
        kwargs = {k: v for k, v in kwargs.items() if k in allowed_args}

    # Filter out None values to let defaults take effect
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    # Call original function with state
    result = func(app.state, **filtered_kwargs)

    # Handle prompt-specific formatting
    component_type = config.get("type")
    if component_type == "prompt":
        return _handle_prompt_result(result, app, meta)

    # Apply formatting for text-based MIME types
    mime_type = str(config.get("mime_type") or "")
    if mime_type.startswith("text/") and meta.display and result is not None:
        return app.formatter.format(result, meta)

    return result


def _handle_prompt_result(result: Any, app: "App", meta: "CommandMeta") -> dict:
    """Convert various result formats to MCP prompt messages.

    Handles:
    - Dict with "messages" key containing elements content
    - String (auto-wrapped as user message)
    - Dict with "elements" key (rendered to markdown)
    - Other types (converted to string)
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
