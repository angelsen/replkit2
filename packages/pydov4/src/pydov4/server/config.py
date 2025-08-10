"""Server configurations for PyDoV4."""

from typing import Any
import logging

logger = logging.getLogger(__name__)


# Server configurations
SERVERS: dict[str, dict[str, Any]] = {
    "basedpyright": {
        "command": ["uv", "run", "basedpyright-langserver", "--stdio"],
        "initialization_options": {},
        "description": "Microsoft's Pyright fork with additional features",
    },
    "pyright": {
        "command": ["uv", "run", "pyright-langserver", "--stdio"],
        "initialization_options": {},
        "description": "Microsoft's Python type checker",
    },
    "ruff": {
        "command": ["uv", "run", "ruff", "server"],
        "initialization_options": {
            "settings": {
                "ruff": {
                    "organizeImports": True,
                }
            }
        },
        "description": "Fast Python linter and formatter",
        # Note: ruff has protocol quirks with NotebookDocumentSyncOptions
        # We handle this gracefully in the client
    },
    "pylsp": {
        "command": ["uv", "run", "pylsp"],
        "initialization_options": {
            "pylsp": {
                "plugins": {
                    "jedi": {"enabled": True},
                    "pylint": {"enabled": False},  # Use ruff instead
                    "pycodestyle": {"enabled": False},  # Use ruff instead
                }
            }
        },
        "description": "Python LSP Server (community implementation)",
    },
}


def get_server_command(server: str) -> list[str] | None:
    """Get the command to start a server.

    Args:
        server: Server name (e.g., 'basedpyright', 'ruff')

    Returns:
        Command list or None if server not found
    """
    config = SERVERS.get(server)
    return config["command"] if config else None


def get_initialization_options(server: str) -> dict[str, Any]:
    """Get initialization options for a server.

    Args:
        server: Server name

    Returns:
        Initialization options dict (empty if none specified)
    """
    config = SERVERS.get(server)
    return config.get("initialization_options", {}) if config else {}


def get_server_description(server: str) -> str:
    """Get description for a server.

    Args:
        server: Server name

    Returns:
        Server description or 'Unknown server'
    """
    config = SERVERS.get(server)
    return config.get("description", "Unknown server") if config else "Unknown server"


def list_available_servers() -> list[str]:
    """List all available servers.

    Returns:
        List of server names
    """
    return list(SERVERS.keys())


def is_server_available(server: str) -> bool:
    """Check if a server is available.

    Args:
        server: Server name

    Returns:
        True if server is configured
    """
    return server in SERVERS
