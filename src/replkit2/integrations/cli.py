"""CLI integration for ReplKit2 applications."""

from typing import Callable, TYPE_CHECKING
import functools

if TYPE_CHECKING:
    from typer import Typer
    from ..app import App
    from ..types.core import CommandMeta


class CLIIntegration:
    """Handles Typer CLI integration for ReplKit2 applications."""

    def __init__(self, app: "App"):
        self.app = app
        self.cli: "Typer | None" = None

    def create_cli(self) -> "Typer":
        """Create Typer CLI from registered commands."""
        if self.cli is None:
            try:
                from typer import Typer
            except ImportError:
                raise ImportError("Typer is required for CLI features. Install it with: pip install typer")

            self.cli = Typer(
                name=self.app.name,
                help=f"{self.app.name} - ReplKit2 application",
                rich_markup_mode="rich",
            )

            self._register_commands()

        return self.cli

    def _register_commands(self):
        """Register all CLI commands with Typer CLI."""
        assert self.cli is not None, "CLI must be created first"

        # Register commands
        for name, (func, meta) in self.app._cli_commands.items():
            if func.__name__ != name:  # Skip aliases for now
                continue
            self._register_command(name, func, meta)

    def _register_command(self, name: str, func: Callable, meta: "CommandMeta"):
        """Register a command with Typer."""
        assert self.cli is not None, "CLI must be initialized"

        typer_config = meta.typer or {}

        # Create wrapper that handles state and formatting
        wrapper = self._create_wrapper(func, meta)

        # Build Typer command decorator arguments
        command_args = {
            "name": typer_config.get("name", name.replace("_", "-")),
            "help": typer_config.get("help", func.__doc__),
            "epilog": typer_config.get("epilog"),
            "short_help": typer_config.get("short_help"),
            "hidden": typer_config.get("hidden", False),
            "rich_help_panel": typer_config.get("rich_help_panel"),
        }

        # Filter out None values
        command_args = {k: v for k, v in command_args.items() if v is not None}

        # Register with Typer
        self.cli.command(**command_args)(wrapper)

    def _create_wrapper(self, func: Callable, meta: "CommandMeta") -> Callable:
        """Create wrapper that handles state injection and output formatting for CLI."""

        @functools.wraps(func)
        def cli_wrapper(*args, **kwargs):
            # Inject state if needed
            if self.app.state is not None:
                result = func(self.app.state, *args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Format and print output
            if result is not None:
                if meta.display:
                    formatted = self.app.formatter.format(result, meta)
                    print(formatted)
                else:
                    print(result)

            return result

        return cli_wrapper
