"""Notebook integration for ReplKit2 - load apps from Jupyter notebooks."""

from typing import TYPE_CHECKING, Any, Dict, List, Tuple
import re
import ast
import nbformat

if TYPE_CHECKING:
    from ..app import App


class NotebookIntegration:
    """Load ReplKit2 apps from Jupyter notebooks with markers."""

    def __init__(self, app: "App"):
        self.app = app
        self._state_class = None
        self._commands = {}

    def load(self, notebook_path: str) -> None:
        """Load commands from notebook into app.

        Markers:
        - # replkit2: state - State class definition
        - # replkit2: command <name> - Command definition
        - # replkit2: continue - Continue from previous cell
        - # replkit2: <value> - Parameter defaults
        """
        cells = self._read_notebook(notebook_path)

        current_command = None
        for cell in cells:
            source = cell.get("source", "")

            # Check for state definition
            if "# replkit2: state" in source:
                self._extract_state(source)

            # Check for command start
            elif match := re.match(r"# replkit2: command (\w+)", source):
                current_command = match.group(1)
                self._start_command(current_command, source)

            # Check for command continuation
            elif "# replkit2: continue" in source and current_command:
                self._continue_command(current_command, source)
            else:
                current_command = None

    def _read_notebook(self, path: str) -> List[Dict]:
        """Read notebook using nbformat and return code cells."""
        with open(path, "r") as f:
            nb = nbformat.read(f, as_version=4)

        cells = []
        for cell in nb.cells:
            if cell.cell_type == "code":
                cells.append({"source": cell.source})

        return cells

    def _extract_state(self, source: str) -> None:
        """Extract state class from cell.

        Pseudocode:
        - Parse AST to find class definition
        - Store for app initialization
        """
        # TODO: Parse source with ast module
        # Find @dataclass decorated class
        # Store as self._state_class
        pass

    def _start_command(self, name: str, source: str) -> None:
        """Start extracting a command.

        Pseudocode:
        - Find command_name = {...} dict
        - Extract parameters with type hints
        - Parse # replkit2: <default> comments
        - Store command body
        """
        self._commands[name] = {
            "config": {},  # Will contain display, fastmcp, cli settings
            "params": [],  # Will contain (name, type, default) tuples
            "body": "",  # Will contain function body
        }

        # TODO: Parse source
        # 1. Find variable assignment matching command name
        # 2. Extract dict literal for config
        # 3. Find typed parameters with defaults from comments
        # 4. Extract remaining code as body

    def _continue_command(self, name: str, source: str) -> None:
        """Continue command from previous cell.

        Pseudocode:
        - Append source to existing command body
        """
        if name in self._commands:
            # TODO: Extract body (skip marker line)
            # Append to self._commands[name]["body"]
            pass

    def _create_function(self, name: str, params: List[Tuple], body: str) -> callable:
        """Create function from extracted parts.

        Pseudocode:
        - Build function string with proper signature
        - Use exec to create function
        - Return callable
        """
        # TODO: Build function dynamically
        # def {name}(state, {params}):
        #     {body}
        #     return {last_expression}

        def placeholder(state, **kwargs):
            return f"Command {name} called"

        return placeholder

    def build(self) -> None:
        """Build all commands and register with app.

        Pseudocode:
        - For each command, create function
        - Register with app.command decorator
        """
        for name, cmd in self._commands.items():
            func = self._create_function(name, cmd["params"], cmd["body"])

            # Register with app
            config = cmd["config"]
            self.app.command(**config)(func)


# Convenience function for standalone usage
def load_notebook_app(notebook_path: str, app_name: str = "notebook_app"):
    """Load a notebook as a ReplKit2 app.

    Usage:
        app = load_notebook_app("examples/notebook/app.ipynb")
        app.run()  # or app.mcp.run() or app.cli()
    """
    from ..app import App

    # TODO: Extract state class from notebook first
    # For now, use a simple default
    from dataclasses import dataclass, field

    @dataclass
    class State:
        data: dict = field(default_factory=dict)

    app = App(app_name, State)
    app.notebook.load(notebook_path)
    return app
