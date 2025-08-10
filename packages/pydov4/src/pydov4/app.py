"""PyDoV4 - Modern LSP REPL using ReplKit2."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from replkit2 import App

if TYPE_CHECKING:
    from .client import AsyncLSPClient


@dataclass
class LSPState:
    """State for PyDoV4 LSP REPL."""

    client: "AsyncLSPClient" = field(init=False)
    current_file: str | None = None
    open_files: dict[str, Path] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the LSP client."""
        from .client import AsyncLSPClient

        self.client = AsyncLSPClient()


# Create the app
app = App("pydo", LSPState)

# Apply custom formatter for PyDoV4-specific formatting
from .formatter import PyDoV4Formatter  # noqa: E402

app = app.using(PyDoV4Formatter())

# Import commands after app is created (they self-register)
from . import commands  # noqa: E402, F401


def main():
    """Entry point for pydo command."""
    app.run(title="PyDoV4 - LSP REPL")


if __name__ == "__main__":
    main()
