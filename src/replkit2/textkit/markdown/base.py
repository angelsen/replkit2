"""Base class for markdown elements."""

from abc import ABC, abstractmethod
from typing import Optional


class MarkdownElement(ABC):
    """Base class for markdown elements.

    Unlike the old system, elements do NOT self-register.
    Registration is handled explicitly in __init__.py.
    
    Elements can opt into features by setting class attributes:
    - supports_truncation: Element can truncate its content
    - supports_transforms: Element can apply data transformations
    """

    element_type: Optional[str] = None
    
    # Feature support flags - elements opt-in by setting these to True
    supports_truncation: bool = False
    supports_transforms: bool = False

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "MarkdownElement":
        """Create element from dictionary representation."""
        pass

    @abstractmethod
    def render(self) -> str:
        """Render element to markdown string."""
        pass

    def to_dict(self) -> dict:
        """Convert element to dictionary representation.

        Default implementation for simple elements.
        Override for complex elements with additional fields.
        """
        result = {"type": self.element_type}

        # Add common attributes if they exist
        for attr in [
            "content",
            "level",
            "language",
            "items",
            "ordered",
            "headers",
            "rows",
            "message",
            "align",
            "truncate",
            "transforms",
        ]:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)

        return result

    def _truncate_value(self, value: str, config: dict) -> str:
        """Apply truncation based on config.

        Config options:
        - max: Maximum length (default: 50)
        - mode: "end" | "middle" | "start" (default: "end")
        """
        if not config or not value:
            return value

        max_len = config.get("max", 50)
        mode = config.get("mode", "end")

        if len(value) <= max_len:
            return value

        if mode == "middle":
            keep_start = (max_len - 3) // 2
            keep_end = max_len - 3 - keep_start
            return f"{value[:keep_start]}...{value[-keep_end:]}"
        elif mode == "start":
            return f"...{value[-(max_len - 3) :]}"
        else:  # end
            return f"{value[: max_len - 3]}..."
