"""Builder utility for constructing markdown data structures."""

from typing import Any


class MarkdownBuilder:
    """Builder for constructing markdown data structures.

    Provides a fluent API for building complex markdown documents
    with elements and optional frontmatter.
    """

    def __init__(self):
        self._elements: list[dict[str, Any]] = []
        self._frontmatter: dict[str, Any] = {}

    def frontmatter(self, **kwargs) -> "MarkdownBuilder":
        """Add or update frontmatter.

        Args:
            **kwargs: Key-value pairs for frontmatter

        Returns:
            Self for method chaining
        """
        self._frontmatter.update(kwargs)
        return self

    def element(self, element_type: str, **kwargs) -> "MarkdownBuilder":
        """Add any element type - works with custom elements too.

        Args:
            element_type: Type of element to add
            **kwargs: Element-specific parameters

        Returns:
            Self for method chaining
        """
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

    def list_(self, items: list[str], ordered: bool = False) -> "MarkdownBuilder":
        """Add a list element."""
        return self.element("list", items=items, ordered=ordered)

    def raw(self, content: str) -> "MarkdownBuilder":
        """Add raw markdown content."""
        return self.element("raw", content=content)

    def table(
        self,
        headers: list[str],
        rows: list[dict],
        align: str = "left",
        truncate: dict[str, dict] | None = None,
        transforms: dict[str, str] | None = None,
    ) -> "MarkdownBuilder":
        """Add a table element with optional truncation and transforms.

        Args:
            headers: Column headers
            rows: Data rows
            align: Column alignment (left/right/center)
            truncate: Per-column truncation config
            transforms: Per-column transform functions

        Returns:
            Self for method chaining
        """
        kwargs = {"headers": headers, "rows": rows, "align": align}
        if truncate:
            kwargs["truncate"] = truncate
        if transforms:
            kwargs["transforms"] = transforms
        return self.element("table", **kwargs)

    def alert(self, message: str, level: str = "warning") -> "MarkdownBuilder":
        """Add an alert element.

        Args:
            message: Alert message text
            level: Severity level (warning/error/info/success)

        Returns:
            Self for method chaining
        """
        return self.element("alert", message=message, level=level)

    def build(self) -> dict[str, Any]:
        """Build the final data structure.

        Returns:
            Dictionary with 'elements' and optionally 'frontmatter'
        """
        result: dict[str, Any] = {"elements": self._elements}
        if self._frontmatter:
            result["frontmatter"] = self._frontmatter
        return result


def markdown() -> MarkdownBuilder:
    """Create a new markdown builder.

    Returns:
        New MarkdownBuilder instance
    """
    return MarkdownBuilder()
