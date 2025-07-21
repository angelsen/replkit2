"""Core App class for ReplKit2."""

from typing import Any, Callable
import inspect

from .serializers import Serializer
from .types import CommandMeta, FastMCPConfig, FastMCPDefaults
from .textkit import TextSerializer, compose, hr, align


class App:
    """Flask-style REPL application with command registration."""

    def __init__(
        self,
        name: str,
        state_class: type | None = None,
        serializer: Serializer | None = None,
        uri_scheme: str | None = None,
        fastmcp: FastMCPDefaults | None = None,
    ):
        self.name = name
        self.state_class = state_class
        self._state = state_class() if state_class else None
        self.serializer = serializer or TextSerializer()
        self.uri_scheme = uri_scheme or name
        self.fastmcp_defaults = fastmcp or {}
        self._commands: dict[str, tuple[Callable[..., Any], CommandMeta]] = {}

        self._fastmcp = None
        self._mcp_components = {"tools": {}, "resources": {}, "prompts": {}}

    def command(
        self,
        display: str | None = None,
        aliases: list[str] | None = None,
        fastmcp: FastMCPConfig | None = None,
        **display_opts: Any,
    ) -> Callable[[Callable], Callable]:
        """
        Flask-style decorator for registering commands.

        Args:
            display: Display type for output formatting
            aliases: Alternative names for the command
            fastmcp: FastMCP configuration dict
            **display_opts: Additional display options
        """

        def decorator(func: Callable) -> Callable:
            meta = CommandMeta(display=display, display_opts=display_opts, aliases=aliases or [], fastmcp=fastmcp)

            self._commands[func.__name__] = (func, meta)

            for alias in meta.aliases:
                self._commands[alias] = (func, meta)

            if fastmcp and fastmcp.get("enabled", True):
                mcp_type = fastmcp.get("type")
                if mcp_type in ("tool", "resource", "prompt"):
                    self._mcp_components[f"{mcp_type}s"][func.__name__] = (func, meta)

            return func

        return decorator

    def execute(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a command and return serialized result."""
        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        func, meta = self._commands[command_name]

        if self._state is not None:
            result = func(self._state, *args, **kwargs)
        else:
            result = func(*args, **kwargs)

        return self.serializer.serialize(result, meta)

    def list_commands(self) -> list[str]:
        """Get list of available commands (excluding aliases)."""
        return [name for name, (func, _) in self._commands.items() if func.__name__ == name]

    def bind(self, namespace: dict[str, Any] | None = None) -> None:
        """Bind command functions to a namespace for REPL use."""
        if namespace is None:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                namespace = frame.f_back.f_globals
            else:
                raise RuntimeError("Cannot determine caller's namespace")

        for name, (func, _) in self._commands.items():
            if func.__name__ != name:
                continue

            def make_wrapper(cmd_name: str) -> Callable[..., Any]:
                def wrapper(*args, **kwargs):
                    result = self.execute(cmd_name, *args, **kwargs)
                    print(result)

                wrapper.__name__ = cmd_name
                wrapper.__doc__ = func.__doc__
                return wrapper

            namespace[name] = make_wrapper(name)

        if "help" not in self._commands:

            def help_command(state=None):
                """Show available commands."""
                return self._generate_help_data()

            meta = CommandMeta(display="table", display_opts={"headers": ["Command", "Description"]})
            self._commands["help"] = (help_command, meta)

            def help_wrapper():
                result = self.execute("help")
                print(result)

            help_wrapper.__name__ = "help"
            help_wrapper.__doc__ = "Show available commands."
            namespace["help"] = help_wrapper

    def using(self, serializer: Serializer) -> "App":
        """Create a new App instance using a different serializer."""
        new_app = App(
            self.name, type(self._state) if self._state else None, serializer, self.uri_scheme, self.fastmcp_defaults
        )
        new_app._state = self._state
        new_app._commands = self._commands
        new_app._mcp_components = self._mcp_components
        return new_app

    def run(self, title: str | None = None, banner: str | None = None):
        """Run the REPL application interactively."""
        import code

        namespace = {"app": self}
        self.bind(namespace)

        if title and not banner:
            banner = compose(
                hr("="), align(title, mode="center"), hr("-"), "Type help() for available commands", "", spacing=0
            )

        code.interact(local=namespace, banner=banner or "")

    @property
    def mcp(self):
        """Get or create FastMCP server from registered components."""
        if self._fastmcp is None:
            self._create_fastmcp()
        return self._fastmcp

    def _create_fastmcp(self):
        """Lazily create FastMCP server."""
        try:
            from fastmcp import FastMCP
        except ImportError:
            raise ImportError("FastMCP is required for MCP features. Install it with: pip install fastmcp")

        self._fastmcp = FastMCP(self.name)

        for name, (func, meta) in self._mcp_components["tools"].items():
            config = {**self.fastmcp_defaults, **meta.fastmcp}
            wrapper = self._create_stateful_wrapper(func)
            self._fastmcp.tool(
                name=config.get("name", name),
                description=config.get("description", func.__doc__),
                tags=config.get("tags"),
                enabled=config.get("enabled", True),
            )(wrapper)

        for name, (func, meta) in self._mcp_components["resources"].items():
            config = {**self.fastmcp_defaults, **meta.fastmcp}
            uri = config.get("uri") or self._generate_uri(func)
            wrapper = self._create_stateful_wrapper(func)
            self._fastmcp.resource(
                uri=uri,
                name=config.get("name", name),
                description=config.get("description", func.__doc__),
                mime_type=config.get("mime_type"),
                tags=config.get("tags"),
                enabled=config.get("enabled", True),
            )(wrapper)

            # Generate stub if requested and URI has parameters
            stub_config = config.get("stub")
            if stub_config and "{" in uri:
                self._register_stub_resource(func, uri, stub_config)

        for name, (func, meta) in self._mcp_components["prompts"].items():
            config = {**self.fastmcp_defaults, **meta.fastmcp}
            wrapper = self._create_stateful_wrapper(func)
            self._fastmcp.prompt(
                name=config.get("name", name),
                description=config.get("description", func.__doc__),
                tags=config.get("tags"),
                enabled=config.get("enabled", True),
            )(wrapper)

    def _generate_uri(self, func):
        """Generate URI template from function signature."""
        sig = inspect.signature(func)
        params = [p for n, p in sig.parameters.items() if n != "state"]

        if not params:
            return f"{self.uri_scheme}://{func.__name__}"

        template_parts = [f"{{{p.name}}}" for p in params if p.default == inspect.Parameter.empty]
        optional_parts = [f"{{{p.name}}}" for p in params if p.default != inspect.Parameter.empty]

        uri = f"{self.uri_scheme}://{func.__name__}"
        if template_parts:
            uri += "/" + "/".join(template_parts)
        if optional_parts:
            uri += "/" + "/".join(optional_parts)

        return uri

    def _create_stateful_wrapper(self, func):
        """Create wrapper that injects state."""
        import functools

        sig = inspect.signature(func)

        new_params = []
        for name, param in sig.parameters.items():
            if name != "state":
                new_params.append(param)

        new_sig = sig.replace(parameters=new_params)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(self._state, *args, **kwargs)

        wrapper.__signature__ = new_sig  # pyright: ignore[reportAttributeAccessIssue]

        return wrapper

    def _generate_help_data(self) -> list[dict[str, str]]:
        """Generate help data for commands."""
        commands = []
        for name, (func, meta) in self._commands.items():
            if func.__name__ != name:
                continue

            sig = inspect.signature(func)
            params = []
            for param_name, param in sig.parameters.items():
                if param_name == "state":
                    continue
                if param.default == inspect.Parameter.empty:
                    params.append(param_name)
                else:
                    params.append(f"{param_name}={param.default!r}")

            signature = f"{name}({', '.join(params)})"

            description = ""
            if func.__doc__:
                description = func.__doc__.strip().split("\n")[0]

            commands.append({"Command": signature, "Description": description})

        return sorted(commands, key=lambda x: x["Command"])

    def _register_stub_resource(self, func, uri_template: str, stub_config: bool | dict[str, Any]):
        """Register a stub resource for a template resource."""
        import re

        # Convert {param} to :param in URI
        stub_uri = re.sub(r"\{(\w+)\}", r":\1", uri_template)

        # Extract first line of docstring for description
        description = ""
        if func.__doc__:
            description = func.__doc__.strip().split("\n")[0]

        # Determine response data
        if isinstance(stub_config, dict) and "response" in stub_config:
            # User provided custom response
            response_data = stub_config["response"]
        else:
            # Minimal default response
            response_data = {
                "description": description,
                "template": uri_template,
            }

        # Create stub function
        async def stub_func():
            return response_data

        # Set function metadata
        stub_func.__name__ = f"{func.__name__}_stub"
        stub_func.__doc__ = f"Example usage for {uri_template}"

        # Register the stub as a regular resource
        if self._fastmcp is not None:
            self._fastmcp.resource(
                uri=stub_uri,
                name=f"{func.__name__}_example",
                description=f"Example usage for {description}" if description else f"Example usage for {uri_template}",
            )(stub_func)
