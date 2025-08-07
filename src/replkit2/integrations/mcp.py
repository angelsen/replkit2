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
        for name, (func, meta) in self.app._mcp_components["tools"].items():
            config = {**self.app.fastmcp_defaults, **meta.fastmcp}
            wrapper = self._create_tool_wrapper(func, meta, config)

            tool_kwargs = {
                "name": config.get("name", name),
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

    def _register_resources(self):
        """Register resources based on their parameter patterns."""
        for name, (func, meta) in self.app._mcp_components["resources"].items():
            config = {**self.app.fastmcp_defaults, **meta.fastmcp}

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
        for name, (func, meta) in self.app._mcp_components["prompts"].items():
            config = {**self.app.fastmcp_defaults, **meta.fastmcp}
            wrapper = self._create_prompt_wrapper(func, meta, config)

            self.server.prompt(
                name=config.get("name", name),
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

        # Register stub if requested
        stub_config = config.get("stub")
        if stub_config:
            self._register_stub_resource(func, uri, stub_config)

    def _register_simple_resource(self, func: Callable, meta, config: dict):
        """Register simple resource with direct parameter mapping."""
        assert self.server is not None, "Server must be created first"
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

    def _create_tool_wrapper(self, func: Callable, meta, config: dict) -> Callable:
        """Create wrapper for tool functions."""
        import functools

        @functools.wraps(func)
        def wrapper(**kwargs):
            return self._call_function_with_formatting(func, kwargs, meta, config)

        # Create signature without state parameter
        wrapper.__signature__ = self._create_simple_signature(func)  # pyright: ignore[reportAttributeAccessIssue]

        return wrapper

    def _create_prompt_wrapper(self, func: Callable, meta, config: dict) -> Callable:
        """Create wrapper for prompt functions."""
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
        # Filter out None values to let defaults take effect
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        # Call original function with state
        result = func(self.app._state, **filtered_kwargs)

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

        # Add required parameters
        for name, param in sig.parameters.items():
            if name != "state" and param.default == inspect.Parameter.empty:
                new_params.append(param)

        # Add greedy params parameter
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
        """Parse greedy parameter string into function kwargs."""
        if not params_string or params_string == "-":
            return {}

        parts = params_string.split("/")
        optional_params = self._get_optional_parameters(func)

        result = {}
        for i, param in enumerate(optional_params):
            if i < len(parts) and parts[i] not in ("", "-"):
                # Pass raw strings - let function handle type conversion
                result[param.name] = parts[i]

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
