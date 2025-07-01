"""ReplKit2: A minimal framework for building stateful REPL applications."""

from typing import Any, Callable
import inspect

from .decorators import state, command
from .serializers import Serializer, JSONSerializer, PassthroughSerializer
from .types import CommandMeta


class App:
    """REPL application with stateful commands."""

    def __init__(self, name: str, serializer: Serializer | None = None):
        self.name = name
        self.serializer = serializer or self._get_default_serializer()
        self._commands: dict[str, tuple[Callable[..., Any], CommandMeta]] = {}
        self._state_instance: Any = None

    def _get_default_serializer(self) -> Serializer:
        """Get the default serializer, preferring TextSerializer if available."""
        try:
            from .textkit import TextSerializer

            return TextSerializer()
        except ImportError:
            return JSONSerializer()

    def register(self, state_class: type) -> None:
        """Register a @state decorated class."""
        if not hasattr(state_class, "__is_state__"):
            raise ValueError(f"{state_class.__name__} must be decorated with @state")

        # Create instance
        self._state_instance = state_class()

        # Extract @command methods
        for name, method in inspect.getmembers(self._state_instance):
            # Check if it's a bound method with the command decorator
            if hasattr(method, "__func__") and hasattr(
                method.__func__, "__is_command__"
            ):
                # Get metadata from the underlying function
                meta = getattr(method.__func__, "__command_meta__", CommandMeta())
                self._commands[name] = (method, meta)

                # Register aliases
                for alias in meta.aliases:
                    self._commands[alias] = (method, meta)

    def execute(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a command and return serialized result."""
        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        method, meta = self._commands[command_name]
        result = method(*args, **kwargs)
        return self.serializer.serialize(result, meta)

    def list_commands(self) -> list[str]:
        """Get list of available commands (excluding aliases)."""
        return [
            name
            for name, (method, _) in self._commands.items()
            if method.__name__ == name
        ]

    def with_serializer(self, serializer: Serializer) -> "App":
        """
        Create a new App view with a different serializer but same state.

        This allows using the same stateful commands with different output formats:

        Example:
            app = create_repl_app("todo", TodoApp)
            json_view = app.with_serializer(JSONSerializer())
            text_view = app.with_serializer(TextSerializer())
        """
        view = App(self.name, serializer)
        view._state_instance = self._state_instance
        view._commands = self._commands
        return view

    def inject_commands(self, namespace: dict[str, Any] | None = None) -> None:
        """
        Inject REPL-friendly command functions into a namespace.

        If namespace is None, injects into the caller's global namespace.
        Each command becomes a function that prints its formatted output.
        """
        if namespace is None:
            # Get the caller's global namespace
            frame = inspect.currentframe()
            if frame and frame.f_back:
                namespace = frame.f_back.f_globals
            else:
                raise RuntimeError("Cannot determine caller's namespace")

        # Create wrapped functions for each command
        for name, (method, _) in self._commands.items():
            # Skip aliases to avoid confusion
            if method.__name__ != name:
                continue

            def make_wrapper(cmd_name: str, cmd_method: Callable[..., Any]) -> Callable[..., Any]:
                def wrapper(*args, **kwargs):
                    result = self.execute(cmd_name, *args, **kwargs)
                    if isinstance(result, str):
                        print(result)
                    else:
                        # For PassthroughSerializer
                        return result

                # Preserve metadata
                wrapper.__name__ = cmd_name
                wrapper.__doc__ = cmd_method.__doc__
                return wrapper

            namespace[name] = make_wrapper(name, method)


def create_repl_app(
    name: str,
    state_class: type,
    serializer: Serializer | None = None,
    inject: bool = True,
) -> App:
    """
    Create a REPL app with a single call.

    This convenience function:
    1. Creates an App instance
    2. Registers the state class
    3. Optionally injects commands into the caller's namespace

    Args:
        name: Application name
        state_class: Class decorated with @state containing commands
        serializer: Optional serializer (defaults to TextSerializer if available)
        inject: Whether to inject commands into caller's namespace

    Returns:
        Configured App instance
    """
    app = App(name, serializer=serializer)
    app.register(state_class)

    if inject:
        # Get the caller's namespace
        frame = inspect.currentframe()
        if frame and frame.f_back:
            app.inject_commands(frame.f_back.f_globals)

    return app


__all__ = [
    "App",
    "create_repl_app",
    "state",
    "command",
    "Serializer",
    "JSONSerializer",
    "PassthroughSerializer",
    "CommandMeta",
]
