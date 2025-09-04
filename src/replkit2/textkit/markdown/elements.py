"""Core markdown elements."""

from .base import MarkdownElement


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
