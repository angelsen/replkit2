"""Execution context types for ReplKit2.

This module provides types for tracking execution context across different
modes (REPL, MCP, CLI, programmatic) to enable adaptive command behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any


class ExecutionMode(str, Enum):
    """Execution mode for command invocation.

    Attributes:
        REPL: Interactive Python REPL session
        MCP: Model Context Protocol (LLM integration)
        CLI: Command-line interface via Typer
        PROGRAMMATIC: Direct execute() calls from code
        TEST: Test execution environment
    """

    REPL = "repl"
    MCP = "mcp"
    CLI = "cli"
    PROGRAMMATIC = "programmatic"
    TEST = "test"


class TransportType(str, Enum):
    """Transport mechanism for command execution.

    Attributes:
        STDIO: Standard input/output
        SSE: Server-sent events
        HTTP: HTTP request/response
        DIRECT: Direct function call (in-process)
        UNKNOWN: Unknown or not applicable
    """

    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    DIRECT = "direct"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ExecutionContext:
    """Context information about command execution.

    Provides commands with awareness of their execution environment, enabling
    adaptive behavior based on whether they're called from a REPL, MCP server,
    CLI, or programmatically.

    Commands opt-in to context by accepting a _ctx parameter:

        @app.command()
        def my_command(state, param: str, _ctx: ExecutionContext = None):
            # Adapt behavior based on context
            if _ctx and _ctx.is_repl():
                return data[:20]  # Limited for terminal
            else:
                return data  # Full dataset for LLM/API

    Context is read-only from the command perspective. All metadata must be
    provided at creation time via factory methods.

    Attributes:
        mode: Execution mode (REPL, MCP, CLI, programmatic, test)
        transport: Transport mechanism (stdio, http, direct, etc.)
        metadata: Immutable mapping of integration-specific data
    """

    mode: ExecutionMode
    transport: TransportType = TransportType.UNKNOWN
    metadata: MappingProxyType[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    # Mode checking helpers

    def is_repl(self) -> bool:
        """Check if execution is in REPL mode.

        Returns:
            True if mode is REPL, False otherwise
        """
        return self.mode == ExecutionMode.REPL

    def is_mcp(self) -> bool:
        """Check if execution is in MCP mode.

        Returns:
            True if mode is MCP (LLM integration), False otherwise
        """
        return self.mode == ExecutionMode.MCP

    def is_cli(self) -> bool:
        """Check if execution is in CLI mode.

        Returns:
            True if mode is CLI, False otherwise
        """
        return self.mode == ExecutionMode.CLI

    def is_programmatic(self) -> bool:
        """Check if execution is programmatic (via app.execute()).

        Returns:
            True if mode is programmatic, False otherwise
        """
        return self.mode == ExecutionMode.PROGRAMMATIC

    def is_interactive(self) -> bool:
        """Check if execution is interactive (REPL).

        Alias for is_repl() for semantic clarity in some contexts.

        Returns:
            True if mode is REPL, False otherwise
        """
        return self.is_repl()

    # Metadata helpers (read-only)

    def get_mime_type(self) -> str | None:
        """Get MIME type from metadata.

        In MCP mode, this returns the MIME type from fastmcp config if set.

        Returns:
            MIME type string if set, None otherwise
        """
        return self.metadata.get("mime_type")

    def get_component_type(self) -> str | None:
        """Get MCP component type from metadata.

        In MCP mode, this indicates whether the command is registered as
        a tool, resource, or prompt.

        Returns:
            Component type ("tool", "resource", "prompt") if set, None otherwise
        """
        return self.metadata.get("component_type")

    # Factory methods

    @classmethod
    def for_repl(cls) -> ExecutionContext:
        """Create context for REPL execution.

        Returns:
            ExecutionContext configured for REPL mode with direct transport
        """
        return cls(mode=ExecutionMode.REPL, transport=TransportType.DIRECT)

    @classmethod
    def for_mcp(
        cls,
        component_type: str,
        mime_type: str | None = None,
        transport: TransportType = TransportType.STDIO,
    ) -> ExecutionContext:
        """Create context for MCP execution.

        Args:
            component_type: MCP component type ("tool", "resource", or "prompt")
            mime_type: Optional MIME type from fastmcp config
            transport: Transport mechanism (default: STDIO)

        Returns:
            ExecutionContext configured for MCP mode with metadata
        """
        metadata_dict = {"component_type": component_type}
        if mime_type is not None:
            metadata_dict["mime_type"] = mime_type

        return cls(
            mode=ExecutionMode.MCP,
            transport=transport,
            metadata=MappingProxyType(metadata_dict),
        )

    @classmethod
    def for_cli(cls) -> ExecutionContext:
        """Create context for CLI execution.

        Returns:
            ExecutionContext configured for CLI mode with direct transport
        """
        return cls(mode=ExecutionMode.CLI, transport=TransportType.DIRECT)

    @classmethod
    def for_programmatic(cls) -> ExecutionContext:
        """Create context for programmatic execution.

        Used when commands are called via app.execute() from code.

        Returns:
            ExecutionContext configured for programmatic mode with direct transport
        """
        return cls(mode=ExecutionMode.PROGRAMMATIC, transport=TransportType.DIRECT)

    @classmethod
    def for_test(cls, **metadata) -> ExecutionContext:
        """Create context for test execution.

        Args:
            **metadata: Custom metadata for test scenarios (e.g., test_name, scenario)

        Returns:
            ExecutionContext configured for test mode with direct transport

        Example:
            >>> ctx = ExecutionContext.for_test()
            >>> ctx.mode
            <ExecutionMode.TEST: 'test'>

            >>> ctx = ExecutionContext.for_test(test_name="test_preview", scenario="repl_simulation")
            >>> ctx.metadata["test_name"]
            'test_preview'
        """
        return cls(
            mode=ExecutionMode.TEST,
            transport=TransportType.DIRECT,
            metadata=MappingProxyType(metadata),
        )
