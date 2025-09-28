"""Main orchestrator for MCP integration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ...app import App

from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts


class FastMCPIntegration:
    """Thin orchestrator for MCP integration with ReplKit2 applications."""

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

            # Extract MCP configuration for server
            config = self.app.mcp_config.copy()

            self.server = FastMCP(
                self.app.name,
                **config,  # Pass all config (instructions, version, tags, etc.)
            )
            self._register_components()

        return self.server

    def _register_components(self):
        """Register all MCP components with FastMCP server."""
        assert self.server is not None, "Server must be created first"

        # Register components using specialized modules
        register_tools(self.server, self.app)
        register_resources(self.server, self.app)
        register_prompts(self.server, self.app)

    def run(self):
        """Run the MCP server."""
        server = self.create_server()
        server.run()
