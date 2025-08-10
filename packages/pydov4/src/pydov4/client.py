"""Async LSP client with thread-based event loop management."""

import asyncio
import threading
from pathlib import Path
from typing import Any
from lsprotocol import types
from pygls.lsp.client import BaseLanguageClient
from .converters import converter_registry


class AsyncLSPClient:
    """Async LSP client that runs in its own thread.

    This client solves the async/sync mismatch by running the LSP client
    in a dedicated background thread with its own event loop.
    """

    def __init__(self):
        self.client: BaseLanguageClient | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self.diagnostics: dict[str, list[Any]] = {}
        self.messages: list[str] = []
        self.server_capabilities: types.ServerCapabilities | None = None

    def _run_loop(self):
        """Run the event loop in a thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._ready.set()
        self.loop.run_forever()

    def _run_async(self, coro):
        """Run a coroutine in the client's loop and return result.

        This is the critical pattern that makes everything work - it runs
        coroutines in the dedicated thread's event loop.
        """
        if not self.loop or not self._thread or not self._thread.is_alive():
            # Start the thread if not running
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self._ready.wait()

        if self.loop is None:
            raise RuntimeError("Event loop not initialized")
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=30.0)

    async def _connect_async(self, server: str) -> dict[str, Any]:
        """Internal async connection logic."""
        from pydov4.server import get_server_command, get_initialization_options

        # Check if server needs a custom converter
        converter_factory = converter_registry.get_converter_factory(server)
        if converter_factory:
            # Pass the factory function itself, not the converter instance
            self.client = BaseLanguageClient("pydov4", "v1", converter_factory=converter_factory)
        else:
            self.client = BaseLanguageClient("pydov4", "v1")

        # Setup handlers for diagnostics and messages
        @self.client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
        def on_diagnostics(params: types.PublishDiagnosticsParams):
            self.diagnostics[params.uri] = params.diagnostics

        @self.client.feature(types.WINDOW_LOG_MESSAGE)
        def on_log(params: types.LogMessageParams):
            self.messages.append(params.message)

        # Get server command from config
        command = get_server_command(server)
        if not command:
            raise ValueError(f"Unknown server: {server}")

        await self.client.start_io(*command)

        # Get initialization options
        init_options = get_initialization_options(server)

        response = await self.client.initialize_async(
            types.InitializeParams(
                process_id=None,
                root_uri=f"file://{Path.cwd()}",
                initialization_options=init_options if init_options else None,
                capabilities=types.ClientCapabilities(
                    text_document=types.TextDocumentClientCapabilities(
                        hover=types.HoverClientCapabilities(),
                        definition=types.DefinitionClientCapabilities(),
                        references=types.ReferenceClientCapabilities(),
                        completion=types.CompletionClientCapabilities(),
                        publish_diagnostics=types.PublishDiagnosticsClientCapabilities(),
                        inlay_hint=types.InlayHintClientCapabilities(),
                    )
                ),
            )
        )

        self.client.initialized(types.InitializedParams())

        # Store server capabilities
        self.server_capabilities = response.capabilities

        return {
            "name": response.server_info.name if response.server_info else server,
            "version": response.server_info.version if response.server_info else "unknown",
            "capabilities": self._summarize_capabilities(response.capabilities),
        }

    def connect(self, server: str) -> dict[str, Any]:
        """Connect to an LSP server."""
        try:
            return self._run_async(self._connect_async(server))
        except Exception as e:
            # Check for known protocol issues
            error_msg = str(e)
            if "NotebookDocumentSyncOptions" in error_msg:
                # Ruff-specific issue
                raise RuntimeError(
                    f"Protocol error: {server} returned unsupported notebook features. "
                    "This is a known issue with some servers. The connection may still work for basic features."
                ) from e
            elif "StructureHandlerNotFoundError" in error_msg:
                # General protocol mismatch
                raise RuntimeError(
                    f"Protocol error: {server} returned data that couldn't be parsed. "
                    "The server may use incompatible LSP extensions."
                ) from e
            else:
                # Re-raise original error
                raise

    async def _disconnect_async(self):
        """Internal async disconnection logic."""
        if self.client:
            await self.client.shutdown_async(None)
            self.client.exit(None)
            await self.client.stop()

    def disconnect(self):
        """Disconnect from the LSP server."""
        if not self.client:
            return
        self._run_async(self._disconnect_async())
        self.client = None
        self.diagnostics.clear()
        self.messages.clear()

    def open_document(self, path: Path) -> str:
        """Open a document and return its URI."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")

        uri = f"file://{path.resolve()}"
        content = path.read_text()

        # Send notification synchronously
        self.client.text_document_did_open(
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(uri=uri, language_id="python", version=0, text=content)
            )
        )

        # Wait a bit for server to process
        self._run_async(asyncio.sleep(0.5))

        return uri

    def close_document(self, uri: str):
        """Close a document."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")

        self.client.text_document_did_close(
            types.DidCloseTextDocumentParams(text_document=types.TextDocumentIdentifier(uri=uri))
        )

    async def _hover_async(self, uri: str, line: int, col: int) -> types.Hover | None:
        """Internal async hover logic."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        return await self.client.text_document_hover_async(
            types.HoverParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line - 1, character=col - 1),
            )
        )

    def hover(self, uri: str, line: int, col: int) -> types.Hover | None:
        """Get hover information at position."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")
        return self._run_async(self._hover_async(uri, line, col))

    async def _definition_async(self, uri: str, line: int, col: int):
        """Internal async definition logic."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        return await self.client.text_document_definition_async(
            types.DefinitionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line - 1, character=col - 1),
            )
        )

    def definition(self, uri: str, line: int, col: int):
        """Get definition location."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")
        return self._run_async(self._definition_async(uri, line, col))

    async def _references_async(self, uri: str, line: int, col: int):
        """Internal async references logic."""
        if self.client is None:
            raise RuntimeError("Client not initialized")
        return await self.client.text_document_references_async(
            types.ReferenceParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=types.Position(line=line - 1, character=col - 1),
                context=types.ReferenceContext(include_declaration=True),
            )
        )

    def references(self, uri: str, line: int, col: int):
        """Find all references."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")
        return self._run_async(self._references_async(uri, line, col))

    def get_diagnostics(self, uri: str) -> list[Any]:
        """Get diagnostics for a file."""
        return self.diagnostics.get(uri, [])

    async def _code_actions_async(self, uri: str, line: int, col: int, diagnostics: list[Any] | None = None):
        """Internal async code actions logic."""
        context = types.CodeActionContext(
            diagnostics=diagnostics or [],
            only=None,  # Get all action kinds
        )

        if self.client is None:
            raise RuntimeError("Client not initialized")
        return await self.client.text_document_code_action_async(
            types.CodeActionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                range=types.Range(
                    start=types.Position(line=line - 1, character=col - 1),
                    end=types.Position(line=line - 1, character=col),
                ),
                context=context,
            )
        )

    def code_actions(self, uri: str, line: int, col: int, diagnostics: list[Any] | None = None):
        """Get code actions (quickfixes, refactorings) at position."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")
        return self._run_async(self._code_actions_async(uri, line, col, diagnostics))

    async def _apply_code_action_async(self, action):
        """Internal async apply code action logic."""
        if isinstance(action, types.Command):
            # It's a command
            if self.client is None:
                raise RuntimeError("Client not initialized")
            return await self.client.workspace_execute_command_async(
                types.ExecuteCommandParams(command=action.command, arguments=action.arguments)
            )
        elif isinstance(action, types.CodeAction):
            # It's a code action
            if action.command:
                # Execute the command
                if self.client is None:
                    raise RuntimeError("Client not initialized")
                return await self.client.workspace_execute_command_async(
                    types.ExecuteCommandParams(command=action.command.command, arguments=action.command.arguments)
                )
            elif action.edit:
                # We can't apply edits directly from the client
                # Return the edit for manual application
                return {"edit": action.edit, "message": "Edit returned - manual application needed"}
        return None

    def apply_code_action(self, action):
        """Apply a code action or command."""
        if not self.client:
            raise RuntimeError("Not connected to LSP server")
        return self._run_async(self._apply_code_action_async(action))

    def _summarize_capabilities(self, caps: types.ServerCapabilities) -> dict[str, bool]:
        """Summarize server capabilities for easy access."""
        return {
            "hover": bool(caps.hover_provider),
            "completion": bool(caps.completion_provider),
            "definition": bool(caps.definition_provider),
            "references": bool(caps.references_provider),
            "diagnostics": True,  # Always supported (push model)
            "pull_diagnostics": bool(getattr(caps, "diagnostic_provider", None)),
            "formatting": bool(caps.document_formatting_provider),
            "rename": bool(caps.rename_provider),
            "code_action": bool(caps.code_action_provider),
            "inlay_hints": bool(getattr(caps, "inlay_hint_provider", None)),
        }
