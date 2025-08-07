"""Core App class for ReplKit2."""

from typing import Any, Callable, TYPE_CHECKING
import inspect

from .formatters import Formatter
from .types.core import CommandMeta, FastMCPConfig, FastMCPDefaults, TyperCLI
from .textkit import TextFormatter, compose, hr, align

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from typer import Typer
    from .integrations.mcp import FastMCPIntegration
    from .integrations.cli import CLIIntegration


class SilentResult:
    """Wrapper that suppresses verbose REPL display while preserving data access."""

    def __init__(self, data: Any, command_name: str | None = None):
        self._data = data
        self._command_name = command_name

    def __repr__(self) -> str:
        # Provide helpful summary instead of full data
        prefix = f"{self._command_name}: " if self._command_name else "Result: "

        if isinstance(self._data, list):
            return f"<{prefix}{len(self._data)} items>"
        elif isinstance(self._data, dict):
            return f"<{prefix}{len(self._data)} fields>"
        elif isinstance(self._data, str):
            if len(self._data) > 50:
                return f"<{prefix}{len(self._data)} chars>"
            return f"<{prefix}{self._data!r}>"
        else:
            return f"<{prefix}{type(self._data).__name__}>"

    def __getattr__(self, name: str) -> Any:
        return getattr(self._data, name)

    def __getitem__(self, key: Any) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @property
    def data(self) -> Any:
        """Access the wrapped data directly."""
        return self._data


class App:
    """Flask-style REPL application with command registration."""

    def __init__(
        self,
        name: str,
        state_class: type | None = None,
        formatter: Formatter | None = None,
        uri_scheme: str | None = None,
        fastmcp: FastMCPDefaults | None = None,
    ):
        self.name = name
        self.state_class = state_class
        self._state = state_class() if state_class else None
        self.formatter = formatter or TextFormatter()
        self.uri_scheme = uri_scheme or name
        self.fastmcp_defaults = fastmcp or {}
        self._commands: dict[str, tuple[Callable[..., Any], CommandMeta]] = {}

        self._mcp_integration: "FastMCPIntegration | None" = None
        self._mcp_components = {"tools": {}, "resources": {}, "prompts": {}}

        self._cli_integration: "CLIIntegration | None" = None
        self._cli_commands: dict[str, tuple[Callable[..., Any], CommandMeta]] = {}

    def command(
        self,
        func: Callable | None = None,
        *,
        display: str | None = None,
        aliases: list[str] | None = None,
        fastmcp: FastMCPConfig | None = None,
        typer: TyperCLI | None = None,
        **display_opts: Any,
    ) -> Callable[[Callable], Callable] | Callable:
        """
        Flask-style decorator for registering commands.

        Args:
            func: Function to decorate (when used without parentheses)
            display: Display type for output formatting
            aliases: Alternative names for the command
            fastmcp: FastMCP configuration dict
            typer: Typer CLI configuration dict
            **display_opts: Additional display options
        """

        def decorator(f: Callable) -> Callable:
            meta = CommandMeta(
                display=display, display_opts=display_opts, aliases=aliases or [], fastmcp=fastmcp, typer=typer
            )

            self._commands[f.__name__] = (f, meta)

            for alias in meta.aliases:
                self._commands[alias] = (f, meta)

            if fastmcp and fastmcp.get("enabled", True):
                mcp_type = fastmcp.get("type")
                if mcp_type in ("tool", "resource", "prompt"):
                    self._mcp_components[f"{mcp_type}s"][f.__name__] = (f, meta)

            # Track CLI commands
            if not typer or typer.get("enabled", True):
                self._cli_commands[f.__name__] = (f, meta)

            return f

        if func is None:
            return decorator
        else:
            return decorator(func)

    def execute(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a command and return raw result."""
        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        func, meta = self._commands[command_name]

        if self._state is not None:
            result = func(self._state, *args, **kwargs)
        else:
            result = func(*args, **kwargs)

        return result

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
                    _, meta = self._commands[cmd_name]
                    formatted = self.formatter.format(result, meta)
                    print(formatted)
                    return SilentResult(result, cmd_name) if result is not None else None

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
                formatted = self.formatter.format(result, meta)
                print(formatted)
                return SilentResult(result, "help") if result is not None else None

            help_wrapper.__name__ = "help"
            help_wrapper.__doc__ = "Show available commands."
            namespace["help"] = help_wrapper

    def using(self, formatter: Formatter) -> "App":
        """Create a new App instance using a different formatter."""
        new_app = App(
            self.name, type(self._state) if self._state else None, formatter, self.uri_scheme, self.fastmcp_defaults
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
    def mcp(self) -> "FastMCP":
        """Get or create FastMCP server from registered components."""
        if self._mcp_integration is None:
            from .integrations.mcp import FastMCPIntegration

            self._mcp_integration = FastMCPIntegration(self)
        return self._mcp_integration.create_server()

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

    @property
    def cli(self) -> "Typer":
        """Get or create Typer CLI from registered commands."""
        if self._cli_integration is None:
            from .integrations.cli import CLIIntegration

            self._cli_integration = CLIIntegration(self)
        return self._cli_integration.create_cli()
