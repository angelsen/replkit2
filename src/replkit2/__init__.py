"""ReplKit2: Flask-style framework for building stateful REPL applications."""

from typing import Any, Callable
import inspect

from .serializers import Serializer, JSONSerializer, PassthroughSerializer
from .types import CommandMeta
from .textkit import TextSerializer, compose, hr, align


class App:
    """Flask-style REPL application with command registration."""

    def __init__(self, name: str, state_class: type | None = None, serializer: Serializer | None = None):
        self.name = name
        self.state_class = state_class
        self.state = state_class() if state_class else None
        self.serializer = serializer or self._get_default_serializer()
        self._commands: dict[str, tuple[Callable[..., Any], CommandMeta]] = {}
        self._auto_help = True

    def _get_default_serializer(self) -> Serializer:
        """Get the default serializer (TextSerializer)."""
        return TextSerializer()

    def command(
        self, display: str | None = None, aliases: list[str] | None = None, **display_opts: Any
    ) -> Callable[[Callable], Callable]:
        """
        Flask-style decorator for registering commands.

        Example:
            @app.command(display="table", headers=["Name", "Age"])
            def list_users(state):
                return [{"name": "Alice", "age": 30}]
        """

        def decorator(func: Callable) -> Callable:
            # Create metadata
            meta = CommandMeta(display=display, display_opts=display_opts, aliases=aliases or [])

            # Register the command
            self._commands[func.__name__] = (func, meta)

            # Register aliases
            for alias in meta.aliases:
                self._commands[alias] = (func, meta)

            # Return the original function unchanged
            return func

        return decorator

    def execute(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a command and return serialized result."""
        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        func, meta = self._commands[command_name]

        # Inject state as first argument if we have state
        if self.state is not None:
            result = func(self.state, *args, **kwargs)
        else:
            result = func(*args, **kwargs)

        return self.serializer.serialize(result, meta)

    def list_commands(self) -> list[str]:
        """Get list of available commands (excluding aliases)."""
        return [name for name, (func, _) in self._commands.items() if func.__name__ == name]

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

    def bind(self, namespace: dict[str, Any] | None = None) -> None:
        """
        Bind command functions to a namespace for REPL use.

        Each command becomes a function that prints its formatted output.
        """
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

        if self._auto_help and "help" not in self._commands:

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
        """
        Create a new App instance using a different serializer.

        This allows using the same stateful commands with different output formats:

            app = App("myapp", MyState)
            json_api = app.using(JSONSerializer())
            text_cli = app.using(TextSerializer())
        """
        new_app = App(self.name, type(self.state) if self.state else None, serializer)
        new_app.state = self.state  # Share the same state instance
        new_app._commands = self._commands  # Share the same commands
        return new_app

    def run(self, title: str | None = None, banner: str | None = None, namespace: dict[str, Any] | None = None):
        """Run the REPL application interactively."""
        import code

        if namespace is None:
            namespace = {}

        namespace["app"] = self

        self.bind(namespace)

        if title and not banner:
            banner = compose(
                hr("="), align(title, mode="center"), hr("-"), "Type help() for available commands", "", spacing=0
            )

        code.interact(local=namespace, banner=banner or "")


# Export public API
__all__ = [
    "App",
    "Serializer",
    "JSONSerializer",
    "PassthroughSerializer",
    "TextSerializer",
    "CommandMeta",
]
