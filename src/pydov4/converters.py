"""Custom converters for handling server-specific protocol quirks."""

from typing import Dict, Callable, Optional, Any
from lsprotocol import types, converters
from cattrs import Converter
import logging

logger = logging.getLogger(__name__)

# Type alias for converter factory functions
ConverterFactory = Callable[[], Converter]


def create_ruff_converter() -> Converter:
    """Create a custom converter for ruff server.

    Ruff sends NotebookDocumentSyncOptions with fields that don't match
    the LSP spec, causing deserialization errors. This converter fixes that.
    """
    # Start with pygls default converter
    converter = converters.get_converter()

    def notebook_sync_hook(obj: Any, _type: type) -> Optional[types.NotebookDocumentSyncOptions]:
        """Handle ruff's non-standard NotebookDocumentSyncOptions."""
        if obj is None:
            return None

        # Log what we're fixing
        logger.debug(f"Fixing NotebookDocumentSyncOptions from ruff: {obj}")

        # Return a minimal valid object instead of trying to parse ruff's data
        # This allows the connection to succeed while avoiding the notebook features
        return types.NotebookDocumentSyncOptions(
            notebook_selector=[]  # Empty selector - we don't use notebook features
        )

    # Register the hook for the problematic type
    converter.register_structure_hook(types.NotebookDocumentSyncOptions, notebook_sync_hook)

    logger.info("Created custom converter for ruff with NotebookDocumentSyncOptions fix")
    return converter


class ConverterRegistry:
    """Registry for server-specific converters."""

    def __init__(self):
        self._converters: Dict[str, ConverterFactory] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default converters for known servers with issues."""
        self.register("ruff", create_ruff_converter)
        # Add more as needed for other servers

    def register(self, server_name: str, factory: ConverterFactory):
        """Register a converter factory for a server."""
        self._converters[server_name] = factory
        logger.debug(f"Registered converter for {server_name}")

    def get_converter_factory(self, server_name: str) -> Optional[ConverterFactory]:
        """Get converter factory for a server, if any."""
        return self._converters.get(server_name)

    def has_converter(self, server_name: str) -> bool:
        """Check if a server has a custom converter."""
        return server_name in self._converters


# Global registry instance
converter_registry = ConverterRegistry()
