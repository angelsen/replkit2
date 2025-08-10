"""Type validation for MCP compatibility.

This module ensures command parameters use types that translate cleanly to MCP's JSON schema,
avoiding 'unknown' parameter types that confuse MCP clients.
"""

from typing import Any, Callable, get_origin, get_args, Union, Literal
import inspect


# Types that work correctly in MCP schemas
PRIMITIVE_TYPES = {str, int, float, bool, list, dict, type(None)}
ALLOWED_ORIGINS = {list, dict, Literal}


def validate_mcp_types(func: Callable) -> None:
    """Validate function parameters for MCP compatibility.

    Ensures:
    - All parameters have type annotations (prevents 'unknown' in MCP)
    - No Optional[T] or Union[T, U] types (causes 'unknown' in MCP)
    - Primitives and properly nested generics are allowed
    - Clear, actionable error messages

    Args:
        func: Function to validate

    Raises:
        TypeError: If parameters use types incompatible with MCP
    """
    sig = inspect.signature(func)

    for param_name, param in sig.parameters.items():
        if param_name == "state":  # Skip state parameter
            continue

        annotation = param.annotation

        # Check for missing annotations (causes 'unknown' in MCP)
        if annotation == inspect.Parameter.empty:
            raise TypeError(
                f"Command '{func.__name__}': Parameter '{param_name}' is missing type annotation.\n"
                f"All parameters must have type hints for MCP compatibility.\n"
                f"Add a type like 'str', 'int', 'bool', 'list', or 'dict'."
            )

        # Validate the type annotation
        if not is_valid_mcp_type(annotation):
            error_msg = get_type_error_message(func.__name__, param_name, annotation)
            raise TypeError(error_msg)


def is_valid_mcp_type(annotation: Any) -> bool:
    """Check if a type annotation is MCP-compatible.

    Valid types:
    - Primitives: str, int, float, bool, list, dict, None
    - Generics: List[T], Dict[K, V] where T, K, V are valid
    - Literal["a", "b", "c"] for enum-like choices
    - Nested generics: List[List[str]], Dict[str, Dict[str, int]]

    Invalid types (cause 'unknown' in MCP):
    - Optional[T] or T | None
    - Union[A, B] or A | B
    - Any
    - Custom classes
    - Callable, Type, etc.

    Args:
        annotation: Type annotation to check

    Returns:
        True if the type is MCP-compatible
    """
    # Primitive types are always valid
    if annotation in PRIMITIVE_TYPES:
        return True

    # Check generic types
    origin = get_origin(annotation)

    # Union types (including Optional) cause 'unknown' in MCP
    if origin is Union:
        return False

    # Any type causes 'unknown' in MCP
    from typing import Any as TypingAny

    if annotation is TypingAny:
        return False

    # Check allowed generic origins
    if origin in ALLOWED_ORIGINS:
        if origin == Literal:
            # Literal is always valid (becomes enum in JSON schema)
            return True

        if origin in (list, dict):
            # Check inner types recursively
            args = get_args(annotation)
            if args:
                # All inner types must be valid
                return all(is_valid_mcp_type(arg) for arg in args)
            # Untyped list/dict is valid
            return True

    # Anything else (custom classes, complex types) is invalid
    return False


def get_type_error_message(func_name: str, param_name: str, annotation: Any) -> str:
    """Generate helpful error message for invalid types.

    Args:
        func_name: Name of the function with invalid parameter
        param_name: Name of the parameter with invalid type
        annotation: The invalid type annotation

    Returns:
        Detailed error message with suggestions
    """
    origin = get_origin(annotation)

    # Special messages for common mistakes
    if origin is Union:
        args = get_args(annotation)
        if type(None) in args:
            # This is Optional[T]
            other_type = next(arg for arg in args if arg is not type(None))
            return (
                f"Command '{func_name}': Parameter '{param_name}' uses Optional[{other_type.__name__}].\n"
                f"Optional types cause 'unknown' in MCP clients.\n"
                f"Use '{other_type.__name__} = None' instead of 'Optional[{other_type.__name__}]'.\n"
                f"Example: def {func_name}(state, {param_name}: {other_type.__name__} = None)"
            )
        else:
            # General Union
            type_names = [get_type_name(arg) for arg in args]
            return (
                f"Command '{func_name}': Parameter '{param_name}' uses Union[{', '.join(type_names)}].\n"
                f"Union types cause 'unknown' in MCP clients.\n"
                f"Consider using a single type with appropriate default value."
            )

    from typing import Any as TypingAny

    if annotation is TypingAny:
        return (
            f"Command '{func_name}': Parameter '{param_name}' uses Any type.\n"
            f"This causes 'unknown' in MCP clients.\n"
            f"Use a specific type like 'dict' for arbitrary data or 'str' for text."
        )

    # Check if it's a custom class
    if hasattr(annotation, "__module__") and not annotation.__module__.startswith("typing"):
        return (
            f"Command '{func_name}': Parameter '{param_name}' uses custom type '{annotation.__name__}'.\n"
            f"Custom classes cause 'unknown' in MCP clients.\n"
            f"Use primitive types (str, int, float, bool, list, dict) or their typed versions "
            f"(List[str], Dict[str, int])."
        )

    # Generic error
    return (
        f"Command '{func_name}': Parameter '{param_name}' uses incompatible type {annotation}.\n"
        f"Use primitive types (str, int, float, bool, list, dict) or their typed versions "
        f"(List[str], Dict[str, int]) for MCP compatibility."
    )


def get_type_name(annotation: Any) -> str:
    """Get readable name for a type annotation.

    Args:
        annotation: Type annotation

    Returns:
        Human-readable type name
    """
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    return str(annotation)


def validate_mcp_resource_params(func: Callable) -> None:
    """Validate resource function parameters follow URI constraints.

    Resources have additional constraints beyond general MCP compatibility:
    - Required params must come first
    - Optional params with List types are OK (parsed from comma-separated)
    - Optional params with Dict types must be LAST (consumes remaining URI segments)
    - Only one Dict-type parameter allowed
    - All params must have type annotations (enforced by validate_mcp_types)

    Args:
        func: Resource function to validate

    Raises:
        TypeError: If parameters violate resource constraints
    """
    # First check general MCP compatibility
    validate_mcp_types(func)

    sig = inspect.signature(func)
    params = [(name, param) for name, param in sig.parameters.items() if name != "state"]

    # Check parameter ordering and constraints
    seen_optional = False
    dict_param = None

    for i, (param_name, param) in enumerate(params):
        is_required = param.default == inspect.Parameter.empty
        annotation = param.annotation
        origin = get_origin(annotation)

        # Check parameter ordering
        if is_required and seen_optional:
            raise TypeError(
                f"Resource '{func.__name__}': Required parameter '{param_name}' "
                f"cannot come after optional parameters.\n"
                f"URI pattern requires: /{{{param_name}}} before optional segments.\n"
                f"Reorder parameters: required → optional → dict (if any)"
            )

        if not is_required:
            seen_optional = True

            # Check if it's a Dict type
            if origin is dict or annotation is dict:
                if dict_param:
                    raise TypeError(
                        f"Resource '{func.__name__}': Multiple dict parameters "
                        f"('{dict_param}' and '{param_name}').\n"
                        f"Only one dict parameter allowed as it consumes all remaining URI segments.\n"
                        f"Consider combining into one dict or using separate resources."
                    )
                dict_param = param_name

                # Dict must be last parameter
                if i < len(params) - 1:
                    remaining = [p[0] for p in params[i + 1 :]]
                    raise TypeError(
                        f"Resource '{func.__name__}': Dict parameter '{param_name}' must be last.\n"
                        f"Parameters after it: {remaining}\n"
                        f"Dict params consume all remaining URI segments (key/value/key/value...).\n"
                        f"Move '{param_name}' to the end or use str type with manual parsing."
                    )


def check_function_compatibility(func: Callable) -> dict[str, Any]:
    """Check a function's MCP compatibility and return detailed report.

    Useful for debugging and testing.

    Args:
        func: Function to check

    Returns:
        Dict with compatibility details for each parameter
    """
    sig = inspect.signature(func)
    report = {"function": func.__name__, "is_compatible": True, "parameters": {}}

    for param_name, param in sig.parameters.items():
        if param_name == "state":
            continue

        param_info = {
            "annotation": str(param.annotation),
            "has_default": param.default != inspect.Parameter.empty,
            "default": param.default if param.default != inspect.Parameter.empty else None,
            "is_valid": False,
            "issue": None,
        }

        if param.annotation == inspect.Parameter.empty:
            param_info["issue"] = "Missing type annotation"
            report["is_compatible"] = False
        elif not is_valid_mcp_type(param.annotation):
            param_info["issue"] = "Type causes 'unknown' in MCP"
            report["is_compatible"] = False
        else:
            param_info["is_valid"] = True

        report["parameters"][param_name] = param_info

    return report
