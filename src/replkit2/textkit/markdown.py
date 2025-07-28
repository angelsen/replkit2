"""Markdown formatter and builder for ReplKit2.

This module provides:
- A markdown formatter that renders elements to markdown syntax
- A builder utility for constructing markdown data structures
- Support for frontmatter and common markdown elements
- Self-registering element system for extensibility
"""

from typing import Any, Dict, Type, Optional
from abc import ABC, abstractmethod


class MarkdownElement(ABC):
    """Base class for markdown elements with self-registration."""

    # Class variable to store all element types
    _registry: Dict[str, Type["MarkdownElement"]] = {}
    element_type: Optional[str] = None

    def __init_subclass__(cls, **kwargs):
        """Called when a class is subclassed - auto-registers element types."""
        super().__init_subclass__(**kwargs)

        # Auto-register if element_type is defined
        if hasattr(cls, "element_type") and cls.element_type:
            MarkdownElement._registry[cls.element_type] = cls

    @classmethod
    def get_element_class(cls, element_type: str) -> Optional[Type["MarkdownElement"]]:
        """Get element class by type."""
        return cls._registry.get(element_type)

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "MarkdownElement":
        """Create element from dictionary."""
        pass

    @abstractmethod
    def render(self) -> str:
        """Render element to markdown string."""
        pass


# Core element implementations


class Text(MarkdownElement):
    """Plain text/paragraph element."""

    element_type = "text"

    def __init__(self, content: str):
        self.content = content

    @classmethod
    def from_dict(cls, data: dict) -> "Text":
        return cls(content=data.get("content", ""))

    def render(self) -> str:
        return self.content


class Heading(MarkdownElement):
    """Heading element with levels 1-6."""

    element_type = "heading"

    def __init__(self, content: str, level: int = 1):
        self.content = content
        self.level = max(1, min(6, level))  # Clamp to 1-6

    @classmethod
    def from_dict(cls, data: dict) -> "Heading":
        return cls(content=data.get("content", ""), level=data.get("level", 1))

    def render(self) -> str:
        return f"{'#' * self.level} {self.content}"


class CodeBlock(MarkdownElement):
    """Fenced code block with optional language."""

    element_type = "code_block"

    def __init__(self, content: str, language: str = ""):
        self.content = content
        self.language = language

    @classmethod
    def from_dict(cls, data: dict) -> "CodeBlock":
        return cls(content=data.get("content", ""), language=data.get("language", ""))

    def render(self) -> str:
        return f"```{self.language}\n{self.content}\n```"


class Blockquote(MarkdownElement):
    """Blockquote element with multi-line support."""

    element_type = "blockquote"

    def __init__(self, content: str):
        self.content = content

    @classmethod
    def from_dict(cls, data: dict) -> "Blockquote":
        return cls(content=data.get("content", ""))

    def render(self) -> str:
        lines = self.content.splitlines()
        return "\n".join(f"> {line}" for line in lines)


class List(MarkdownElement):
    """List element (ordered or unordered)."""

    element_type = "list"

    def __init__(self, items: list[str], ordered: bool = False):
        self.items = items
        self.ordered = ordered

    @classmethod
    def from_dict(cls, data: dict) -> "List":
        return cls(items=data.get("items", []), ordered=data.get("ordered", False))

    def render(self) -> str:
        if not self.items:
            return ""

        lines = []
        for i, item in enumerate(self.items, 1):
            prefix = f"{i}." if self.ordered else "-"
            # Handle multi-line list items
            if isinstance(item, str):
                item_lines = item.splitlines()
                lines.append(f"{prefix} {item_lines[0]}")
                # Indent continuation lines
                for line in item_lines[1:]:
                    lines.append(f"  {line}")
            else:
                lines.append(f"{prefix} {item}")

        return "\n".join(lines)


class Raw(MarkdownElement):
    """Raw markdown passthrough - escape hatch for unsupported syntax."""

    element_type = "raw"

    def __init__(self, content: str):
        self.content = content

    @classmethod
    def from_dict(cls, data: dict) -> "Raw":
        return cls(content=data.get("content", ""))

    def render(self) -> str:
        return self.content


def format_markdown(data: dict, meta: Any, formatter: Any) -> str:
    """Format data with 'elements' and optional 'frontmatter' fields as markdown.

    Args:
        data: Dict with 'elements' list and optional 'frontmatter' dict
        meta: Command metadata (unused for markdown)
        formatter: Parent formatter instance (unused for markdown)

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
                    rendered = _render_element(element)
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


def _render_element(element_dict: dict) -> str:
    """Render a single markdown element using the registry."""
    element_type = element_dict.get("type", "")
    element_class = MarkdownElement.get_element_class(element_type)

    if element_class:
        try:
            element = element_class.from_dict(element_dict)
            return element.render()
        except Exception:
            # If rendering fails, return empty string
            return ""

    # Unknown element type - ignore silently
    return ""


class MarkdownBuilder:
    """Builder for constructing markdown data structures."""

    def __init__(self):
        self._elements: list[dict[str, Any]] = []
        self._frontmatter: dict[str, Any] = {}

    def frontmatter(self, **kwargs) -> "MarkdownBuilder":
        """Add or update frontmatter."""
        self._frontmatter.update(kwargs)
        return self

    def element(self, element_type: str, **kwargs) -> "MarkdownBuilder":
        """Add any element type - works with custom elements too."""
        self._elements.append({"type": element_type, **kwargs})
        return self

    # Convenience methods for common elements
    def text(self, content: str) -> "MarkdownBuilder":
        """Add a text/paragraph element."""
        return self.element("text", content=content)

    def heading(self, content: str, level: int = 1) -> "MarkdownBuilder":
        """Add a heading element."""
        return self.element("heading", content=content, level=level)

    def code_block(self, content: str, language: str = "") -> "MarkdownBuilder":
        """Add a code block element."""
        return self.element("code_block", content=content, language=language)

    def blockquote(self, content: str) -> "MarkdownBuilder":
        """Add a blockquote element."""
        return self.element("blockquote", content=content)

    def list(self, items: list[str], ordered: bool = False) -> "MarkdownBuilder":
        """Add a list element."""
        return self.element("list", items=items, ordered=ordered)

    def raw(self, content: str) -> "MarkdownBuilder":
        """Add raw markdown content."""
        return self.element("raw", content=content)

    def build(self) -> dict[str, Any]:
        """Build the final data structure."""
        result: dict[str, Any] = {"elements": self._elements}
        if self._frontmatter:
            result["frontmatter"] = self._frontmatter
        return result


def markdown() -> MarkdownBuilder:
    """Create a new markdown builder."""
    return MarkdownBuilder()


def get_registered_elements() -> Dict[str, Type[MarkdownElement]]:
    """Get all registered markdown element types.

    Useful for debugging and discovering available elements.
    """
    return MarkdownElement._registry.copy()
