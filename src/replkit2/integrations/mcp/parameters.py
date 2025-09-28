"""Parameter analysis and parsing for MCP components."""

import inspect
from typing import Any, Callable, get_origin, get_args


class ParameterAnalyzer:
    """Analyze function parameters for MCP registration strategies."""

    def is_all_optional(self, func: Callable) -> bool:
        """Check if all function parameters (except state) are optional."""
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == "state":  # Skip state parameter
                continue
            if param.default == inspect.Parameter.empty:  # No default = required
                return False
        return True

    def has_optional_parameters(self, func: Callable) -> bool:
        """Check if function has any optional parameters."""
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == "state":  # Skip state parameter
                continue
            if param.default != inspect.Parameter.empty:  # Has default = optional
                return True
        return False

    def get_required_parameters(self, func: Callable) -> list[inspect.Parameter]:
        """Get list of required parameters (excluding state)."""
        sig = inspect.signature(func)
        return [
            param
            for name, param in sig.parameters.items()
            if name != "state" and param.default == inspect.Parameter.empty
        ]

    def get_optional_parameters(self, func: Callable) -> list[inspect.Parameter]:
        """Get list of optional parameters (excluding state)."""
        sig = inspect.signature(func)
        return [
            param
            for name, param in sig.parameters.items()
            if name != "state" and param.default != inspect.Parameter.empty
        ]


def parse_greedy_params(func: Callable, params_string: str) -> dict[str, Any]:
    """Parse greedy parameter string with smart type conversion.

    Handles:
    - Primitives: int, float, bool, str
    - Lists: comma-separated values → List[T]
    - Dicts: last param gets remaining segments as key/value pairs
    - "-" means use default value (skip parameter)
    """
    if not params_string or params_string == "-":
        return {}

    parts = params_string.split("/")
    analyzer = ParameterAnalyzer()
    optional_params = analyzer.get_optional_parameters(func)
    result = {}

    for i, param in enumerate(optional_params):
        if i >= len(parts):
            break

        value = parts[i]

        # Skip "-" to use default value
        if value == "-":
            continue

        # Empty string also means skip
        if value == "":
            continue

        origin = get_origin(param.annotation)
        is_last = i == len(optional_params) - 1
        is_dict = origin is dict or param.annotation is dict

        # Check if dict param should consume remaining segments
        if is_last and is_dict and i < len(parts) - 1:
            # Dict parameter consumes all remaining segments
            remaining = parts[i:]
            if len(remaining) >= 2 and len(remaining) % 2 == 0:
                # Parse as key/value pairs
                value = {}
                for j in range(0, len(remaining), 2):
                    key = remaining[j]
                    val = remaining[j + 1]
                    # For now, keep as strings (can enhance later)
                    value[key] = val
            else:
                # Can't parse as dict, use empty dict
                value = {}
        else:
            # Normal parameter conversion
            if param.annotation != inspect.Parameter.empty:
                try:
                    if param.annotation is int:
                        value = int(value)
                    elif param.annotation is float:
                        value = float(value)
                    elif param.annotation is bool:
                        # URI boolean: accept 'true' (case-insensitive) or '1'
                        value = value.lower() in ("true", "1")
                    elif origin is list:
                        # Parse comma-separated values
                        if value:
                            value = [v.strip() for v in value.split(",")]
                            # Try to convert inner types
                            args = get_args(param.annotation)
                            if args:
                                inner_type = args[0]
                                if inner_type is int:
                                    value = [int(v) for v in value]
                                elif inner_type is float:
                                    value = [float(v) for v in value]
                                elif inner_type is bool:
                                    value = [v.lower() in ("true", "1") for v in value]
                                # str stays as is
                        else:
                            value = []
                    # str passes through as-is
                except (ValueError, TypeError):
                    # If conversion fails, pass the string value
                    pass

        result[param.name] = value

        # If dict consumed everything, stop
        if is_last and is_dict and i < len(parts) - 1:
            break

    return result


class SignatureBuilder:
    """Build and manipulate function signatures for MCP components."""

    @staticmethod
    def without_state(func: Callable) -> inspect.Signature:
        """Create signature without state parameter."""
        sig = inspect.signature(func)
        new_params = [param for name, param in sig.parameters.items() if name != "state"]
        return sig.replace(parameters=new_params)

    @staticmethod
    def with_greedy_params(func: Callable) -> inspect.Signature:
        """Create signature with params parameter for greedy matching."""
        sig = inspect.signature(func)
        new_params = []

        # Add all parameters except state (both required and optional)
        for name, param in sig.parameters.items():
            if name != "state":
                new_params.append(param)

        # Add greedy params parameter for capturing remaining URI segments
        params_param = inspect.Parameter("params", inspect.Parameter.POSITIONAL_OR_KEYWORD, default="", annotation=str)
        new_params.append(params_param)

        return sig.replace(parameters=new_params)
