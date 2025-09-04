"""Alert/warning element for important messages."""

from .base import MarkdownElement
from ..icons import ICONS


class Alert(MarkdownElement):
    """Alert/warning element for important messages.

    Creates styled alert messages with appropriate icons and formatting
    for different severity levels.
    """

    element_type = "alert"

    def __init__(self, message: str, level: str = "warning"):
        """Initialize alert with message and severity level.

        Args:
            message: Alert message text to display.
            level: Severity level (warning/error/info/success). Defaults to "warning".
        """
        self.message = message
        self.level = level

    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Create Alert instance from dictionary data."""
        return cls(message=data.get("message", ""), level=data.get("level", "warning"))

    def render(self) -> str:
        """Render alert as markdown text with appropriate icon."""
        # Map levels to ASCII icons from the ICONS registry
        icon_map = {
            "success": ICONS["success"],  # [OK]
            "error": ICONS["error"],  # [!!]
            "warning": ICONS["warning"],  # [!]
            "info": ICONS["info"],  # [i]
        }

        # Default to bullet if level not recognized
        icon = icon_map.get(self.level, ICONS["bullet"])

        return f"{icon} **{self.message}**"
