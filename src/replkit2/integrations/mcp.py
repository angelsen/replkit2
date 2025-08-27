"""MCP integration for ReplKit2 applications following FastMCP principles."""

from typing import Any, Callable, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..app import App


class FastMCPIntegration:
    """Handles FastMCP integration for ReplKit2 applications."""

    def __init__(self, app: "App"):
        self.app = app
        self.server: "FastMCP | None" = None

    def create_server(self) -> "FastMCP":
        """Create FastMCP server from registered components."""
        if self.server is None:
            try:
                from fastmcp import FastMCP
            except ImportError:
                raise ImportError("FastMCP is required for MCP features. Install it with: pip install fastmcp")

            self.server = FastMCP(self.app.name)
            self._register_components()

        return self.server

    def _register_components(self):
        """Register all MCP components with FastMCP server."""
        assert self.server is not None, "Server must be created first"

        # Register tools
        self._register_tools()

        # Register resources based on parameter patterns
        self._register_resources()

        # Register prompts
        self._register_prompts()

    def _register_tools(self):
        """Register tools with FastMCP server."""
        assert self.server is not None, "Server must be created first"
        for key, item in self.app._mcp_components["tools"].items():
            # Handle both old (func, meta) and new (func, meta, config) formats
            if len(item) == 3:
                func, meta, config = item
                config = {**self.app.fastmcp_defaults, **config}
            else:
                func, meta = item
                config = {**self.app.fastmcp_defaults, **meta.fastmcp}

            # Extract function name from key (might be tuple)
            func_name = key if isinstance(key, str) else key[0]

            wrapper = self._create_wrapper(func, meta, config)

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

            self.server.tool(**tool_kwargs)(wrapper)

            # Register aliases if specified
            aliases = config.get("aliases", [])
            for alias in aliases:
                self._register_tool_alias(func, meta, config, alias)

    def _register_resources(self):
        """Register resources based on their parameter patterns."""
        from ..validation import validate_mcp_resource_params

        for key, item in self.app._mcp_components["resources"].items():
            # Handle both old (func, meta) and new (func, meta, config) formats
            if len(item) == 3:
                func, meta, config = item
                config = {**self.app.fastmcp_defaults, **config}
            else:
                func, meta = item
                config = {**self.app.fastmcp_defaults, **meta.fastmcp}

            # Check for explicit args override
            if "args" in config and not config.get("args"):
                # Empty args list - force no parameters
                self._register_simple_resource(func, meta, config)
                continue

            # Validate resource parameters follow URI constraints
            validate_mcp_resource_params(func)

            if self._is_all_optional_function(func):
                # All-optional: dual registration (base + template)
                self._register_all_optional_resource(func, meta, config)
            elif self._has_optional_parameters(func):
                # Mixed: single registration with greedy pattern
                self._register_greedy_resource(func, meta, config)
            else:
                # Simple: direct registration
                self._register_simple_resource(func, meta, config)

    def _register_prompts(self):
        """Register prompts with FastMCP server."""
        assert self.server is not None, "Server must be created first"
        for key, item in self.app._mcp_components["prompts"].items():
            # Handle both old (func, meta) and new (func, meta, config) formats
            if len(item) == 3:
                func, meta, config = item
                config = {**self.app.fastmcp_defaults, **config}
            else:
                func, meta = item
                config = {**self.app.fastmcp_defaults, **meta.fastmcp}

            # Extract function name from key
            func_name = key if isinstance(key, str) else key[0]

            wrapper = self._create_wrapper(func, meta, config)

            self.server.prompt(
                name=config.get("name", func_name),
                description=config.get("description", func.__doc__),
                tags=config.get("tags"),
                enabled=config.get("enabled", True),
            )(wrapper)

    # === Resource Registration Strategies ===

    def _register_all_optional_resource(self, func: Callable, meta, config: dict):
        """Register dual resources for all-optional functions."""
        assert self.server is not None, "Server must be created first"
        base_uri = f"{self.app.uri_scheme}://{func.__name__}"
        name = func.__name__

        # 1. Base Resource (no parameters - all defaults)
        def base_wrapper():
            return self._call_function_with_formatting(func, {}, meta, config)

        base_wrapper.__name__ = f"{name}_base"
        base_wrapper.__doc__ = f"{func.__doc__} (with all defaults)"

        self.server.resource(
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
            kwargs = self._parse_greedy_params(func, params)
            return self._call_function_with_formatting(func, kwargs, meta, config)

        template_wrapper.__name__ = f"{name}_template"
        template_wrapper.__doc__ = f"{func.__doc__} (with parameters)"

        self.server.resource(
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
            self._register_stub_resource(func, template_uri, stub_config)

    def _register_greedy_resource(self, func: Callable, meta, config: dict):
        """Register single resource with greedy pattern for mixed parameter functions."""
        assert self.server is not None, "Server must be created first"
        uri = config.get("uri") or self._generate_greedy_uri(func)

        def wrapper(**kwargs):
            # Handle greedy params parameter
            if "params" in kwargs:
                params_str = kwargs.pop("params", "")
                if params_str:
                    parsed = self._parse_greedy_params(func, params_str)
                    kwargs.update(parsed)

            # Filter dash placeholders
            kwargs = {k: v for k, v in kwargs.items() if v != "-"}

            return self._call_function_with_formatting(func, kwargs, meta, config)

        # Set proper signature for FastMCP validation
        wrapper.__signature__ = self._create_greedy_signature(func)  # pyright: ignore[reportFunctionMemberAccess]
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        # Copy annotations excluding 'state' and add 'params' for proper type hint support
        original_annotations = getattr(func, "__annotations__", {})
        wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k != "state"}
        wrapper.__annotations__["params"] = str  # Add params annotation for greedy matching

        self.server.resource(
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
            self._register_stub_resource(func, uri, stub_config)

    def _register_simple_resource(self, func: Callable, meta, config: dict):
        """Register simple resource with direct parameter mapping."""
        assert self.server is not None, "Server must be created first"

        # Handle explicit empty args
        if "args" in config and not config["args"]:
            uri = f"{self.app.uri_scheme}://{func.__name__}"
        else:
            uri = config.get("uri") or self._generate_simple_uri(func)

        def wrapper(**kwargs):
            # Filter dash placeholders
            kwargs = {k: v for k, v in kwargs.items() if v != "-"}
            return self._call_function_with_formatting(func, kwargs, meta, config)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__signature__ = self._create_simple_signature(func)  # pyright: ignore[reportFunctionMemberAccess]

        # Copy annotations excluding 'state' for proper type hint support
        original_annotations = getattr(func, "__annotations__", {})
        wrapper.__annotations__ = {k: v for k, v in original_annotations.items() if k != "state"}

        self.server.resource(
            uri=uri,
            name=config.get("name", func.__name__),
            description=config.get("description", func.__doc__),
            mime_type=config.get("mime_type"),
            tags=config.get("tags"),
            enabled=config.get("enabled", True),
        )(wrapper)

    # === Wrapper Creation ===

    def _create_wrapper(self, func: Callable, meta, config: dict) -> Callable:
        """Create wrapper for MCP functions (tools, prompts, etc.)."""
        import functools

        @functools.wraps(func)
        def wrapper(**kwargs):
            return self._call_function_with_formatting(func, kwargs, meta, config)

        # Create signature without state parameter
        wrapper.__signature__ = self._create_simple_signature(func)  # pyright: ignore[reportAttributeAccessIssue]

        return wrapper

    # === Function Calling with Formatting ===

    def _call_function_with_formatting(self, func: Callable, kwargs: dict, meta, config: dict):
        """Call function with state injection and apply formatting if needed."""
        # Filter to allowed args if specified
        if "args" in config:
            allowed_args = config["args"]
            kwargs = {k: v for k, v in kwargs.items() if k in allowed_args}

        # Filter out None values to let defaults take effect
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        # Call original function with state
        result = func(self.app.state, **filtered_kwargs)

        # Apply formatting for text-based MIME types
        mime_type = str(config.get("mime_type") or "")
        if mime_type.startswith("text/") and meta.display and result is not None:
            return self.app.formatter.format(result, meta)

        return result

    # === Parameter Analysis ===

    def _is_all_optional_function(self, func: Callable) -> bool:
        """Check if all function parameters (except state) are optional."""
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == "state":  # Skip state parameter
                continue
            if param.default == inspect.Parameter.empty:  # No default = required
                return False
        return True

    def _has_optional_parameters(self, func: Callable) -> bool:
        """Check if function has any optional parameters."""
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == "state":  # Skip state parameter
                continue
            if param.default != inspect.Parameter.empty:  # Has default = optional
                return True
        return False

    def _get_required_parameters(self, func: Callable) -> list[inspect.Parameter]:
        """Get list of required parameters (excluding state)."""
        sig = inspect.signature(func)
        return [
            param
            for name, param in sig.parameters.items()
            if name != "state" and param.default == inspect.Parameter.empty
        ]

    def _get_optional_parameters(self, func: Callable) -> list[inspect.Parameter]:
        """Get list of optional parameters (excluding state)."""
        sig = inspect.signature(func)
        return [
            param
            for name, param in sig.parameters.items()
            if name != "state" and param.default != inspect.Parameter.empty
        ]

    # === URI Generation ===

    def _generate_greedy_uri(self, func: Callable) -> str:
        """Generate URI with greedy pattern for mixed parameter functions."""
        base_uri = f"{self.app.uri_scheme}://{func.__name__}"
        required_params = self._get_required_parameters(func)

        if required_params:
            base_uri += "/" + "/".join(f"{{{p.name}}}" for p in required_params)

        # Add greedy pattern for optional parameters
        base_uri += "/{params*}"

        return base_uri

    def _generate_simple_uri(self, func: Callable) -> str:
        """Generate URI with direct parameter mapping."""
        base_uri = f"{self.app.uri_scheme}://{func.__name__}"
        required_params = self._get_required_parameters(func)

        if required_params:
            base_uri += "/" + "/".join(f"{{{p.name}}}" for p in required_params)

        return base_uri

    # === Signature Creation ===

    def _create_greedy_signature(self, func: Callable) -> inspect.Signature:
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

    def _create_simple_signature(self, func: Callable) -> inspect.Signature:
        """Create signature without state parameter."""
        sig = inspect.signature(func)
        new_params = [param for name, param in sig.parameters.items() if name != "state"]
        return sig.replace(parameters=new_params)

    # === Parameter Parsing ===

    def _parse_greedy_params(self, func: Callable, params_string: str) -> dict[str, Any]:
        """Parse greedy parameter string with smart type conversion.

        Handles:
        - Primitives: int, float, bool, str
        - Lists: comma-separated values → List[T]
        - Dicts: last param gets remaining segments as key/value pairs
        - "-" means use default value (skip parameter)
        """
        if not params_string or params_string == "-":
            return {}

        from typing import get_origin, get_args

        parts = params_string.split("/")
        optional_params = self._get_optional_parameters(func)
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
                        # Try to convert dict values to appropriate types
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

    # === Stub Registration ===

    def _register_stub_resource(self, func: Callable, uri_template: str, stub_config):
        """Register stub resource with example usage."""
        assert self.server is not None, "Server must be created first"
        # Generate stub URI with enhanced notation
        stub_uri = self._generate_stub_uri(func, uri_template)

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

        self.server.resource(
            uri=stub_uri,
            name=f"{func.__name__}_example",
            description=f"Example usage for {func.__name__}",
        )(stub_func)

    def _generate_stub_uri(self, func: Callable, uri_template: str) -> str:
        """Generate enhanced stub URI with bracketed optional parameters."""
        import re

        if "{params*}" in uri_template:
            # For greedy URIs, show parameter structure
            base = uri_template.replace("/{params*}", "")
            optional_params = self._get_optional_parameters(func)

            for param in optional_params:
                base += f"/[:{param.name}]"

            return base
        else:
            # Standard parameter substitution
            return re.sub(r"\{(\w+)\}", r":\1", uri_template)

    # === Tool Alias Registration ===

    def _register_tool_alias(self, func: Callable, meta, config: dict, alias):
        """Register a tool alias with optional parameter mapping and custom description."""
        assert self.server is not None, "Server must be created first"

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
            wrapper = self._create_mapped_tool_wrapper(func, meta, config, param_mapping)
        else:
            # Use standard wrapper
            wrapper = self._create_wrapper(func, meta, config)

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
        self.server.tool(**tool_kwargs)(wrapper)

    def _create_mapped_tool_wrapper(self, func: Callable, meta, config: dict, param_mapping: dict) -> Callable:
        """Create a tool wrapper with parameter name mapping."""
        import functools

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
            return self._call_function_with_formatting(func, original_kwargs, meta, config)

        # Apply the new signature and annotations
        wrapper.__signature__ = sig.replace(parameters=new_params)  # pyright: ignore[reportAttributeAccessIssue]
        wrapper.__annotations__ = new_annotations

        return wrapper
