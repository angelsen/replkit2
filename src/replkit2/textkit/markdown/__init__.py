"""Markdown module for ReplKit2.

This module provides:
- Markdown elements with rendering support
- Table element with truncation and transforms
- Alert element for important messages
- Builder utility for constructing markdown documents
- Common data transformations (size, timestamp, etc.)
"""

from typing import Any, Type, Optional

# Import base and elements
from .base import MarkdownElement
from .elements import Text, Heading, CodeBlock, Blockquote, List, Raw
from .table import Table
from .alert import Alert
from .builder import MarkdownBuilder, markdown
from .transforms import (
    apply_transform,
    register_transform,
    format_size,
    format_timestamp,
    format_number,
    format_duration,
    format_percentage,
    format_boolean,
    TRANSFORMS,
)

# Element registry - explicit registration instead of auto-registration
_ELEMENT_REGISTRY: dict[str, Type[MarkdownElement]] = {
    "text": Text,
    "heading": Heading,
    "code_block": CodeBlock,
    "blockquote": Blockquote,
    "list": List,
    "raw": Raw,
    "table": Table,
    "alert": Alert,
}


def get_element_class(element_type: str) -> Optional[Type[MarkdownElement]]:
    """Get element class by type.

    Args:
        element_type: Type of element to get

    Returns:
        Element class or None if not found
    """
    return _ELEMENT_REGISTRY.get(element_type)


def register_element(element_type: str, element_class: Type[MarkdownElement]):
    """Register a custom element type.

    Args:
        element_type: Type identifier for the element
        element_class: Element class (must inherit from MarkdownElement)
    """
    _ELEMENT_REGISTRY[element_type] = element_class


def format_markdown(data: dict, meta: Any = None, formatter: Any = None) -> str:
    """Format data with 'elements' and optional 'frontmatter' fields as markdown.

    Command-level truncate/transforms from meta are applied to supporting elements.

    Args:
        data: Dict with 'elements' list and optional 'frontmatter' dict
        meta: Command metadata with optional truncate/transforms settings
        formatter: Parent formatter instance (optional, for future use)

    Returns:
        Formatted markdown string
    """
    sections = []

    # Handle frontmatter if present
    if "frontmatter" in data and data["frontmatter"]:
        sections.append(_render_frontmatter(data["frontmatter"]))

    # Handle elements
    if "elements" in data:
        elements = data["elements"]
        if isinstance(elements, list):
            for element in elements:
                if isinstance(element, dict) and "type" in element:
                    rendered = _render_element(element, meta)  # Pass meta for truncation/transforms
                    if rendered:
                        sections.append(rendered)

    return "\n\n".join(sections)


def _render_frontmatter(frontmatter: dict) -> str:
    """Render frontmatter as YAML front matter."""
    lines = ["---"]
    for key, value in frontmatter.items():
        # Simple YAML rendering - quote strings with special chars
        if isinstance(value, str) and (":" in value or "\n" in value):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _apply_command_settings(element_dict: dict, element_class: Type[MarkdownElement], meta: Any) -> dict:
    """Apply command-level settings to element if it supports them.

    Args:
        element_dict: Original element data
        element_class: Class of the element being created
        meta: Command metadata with truncate/transforms

    Returns:
        Enriched element dict with command settings applied
    """
    # No meta, return original
    if not meta:
        return element_dict

    # Check what this element supports and what command provides
    needs_copy = False
    enriched = element_dict

    # Apply truncation if element supports it and doesn't have its own
    if (
        element_class.supports_truncation
        and hasattr(meta, "truncate")
        and meta.truncate
        and "truncate" not in element_dict
    ):
        if not needs_copy:
            enriched = element_dict.copy()
            needs_copy = True
        enriched["truncate"] = meta.truncate

    # Apply transforms if element supports it and doesn't have its own
    if (
        element_class.supports_transforms
        and hasattr(meta, "transforms")
        and meta.transforms
        and "transforms" not in element_dict
    ):
        if not needs_copy:
            enriched = element_dict.copy()
            needs_copy = True
        enriched["transforms"] = meta.transforms

    return enriched


def _render_element(element_dict: dict, meta: Any = None) -> str:
    """Render a single markdown element using the registry.

    Args:
        element_dict: Element data dictionary
        meta: Command metadata containing truncate/transforms (optional)
    """
    element_type = element_dict.get("type", "")
    element_class = get_element_class(element_type)

    if element_class:
        try:
            # Apply command-level settings based on element capabilities
            enriched_dict = _apply_command_settings(element_dict, element_class, meta)
            element = element_class.from_dict(enriched_dict)
            return element.render()
        except Exception:
            # If rendering fails, return empty string
            return ""

    # Unknown element type - ignore silently
    return ""


def get_registered_elements() -> dict[str, Type[MarkdownElement]]:
    """Get all registered markdown element types.

    Useful for debugging and discovering available elements.

    Returns:
        Dictionary of element types to classes
    """
    return _ELEMENT_REGISTRY.copy()


# Public API exports
__all__ = [
    # Base class
    "MarkdownElement",
    # Core elements
    "Text",
    "Heading",
    "CodeBlock",
    "Blockquote",
    "List",
    "Raw",
    # New elements
    "Table",
    "Alert",
    # Builder
    "MarkdownBuilder",
    "markdown",
    # Transforms
    "apply_transform",
    "register_transform",
    "format_size",
    "format_timestamp",
    "format_number",
    "format_duration",
    "format_percentage",
    "format_boolean",
    "TRANSFORMS",
    # Functions
    "format_markdown",
    "get_element_class",
    "register_element",
    "get_registered_elements",
]
