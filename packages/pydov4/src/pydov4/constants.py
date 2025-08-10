"""Constants and utilities for PyDoV4."""

from enum import StrEnum


class Severity(StrEnum):
    """LSP diagnostic severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"

    @classmethod
    def from_lsp(cls, value: int) -> "Severity":
        """Convert LSP numeric severity to Severity enum."""
        mapping = {
            1: cls.ERROR,
            2: cls.WARNING,
            3: cls.INFO,
            4: cls.HINT,
        }
        return mapping.get(value, cls.INFO)

    def to_lsp(self) -> int:
        """Convert Severity enum to LSP numeric value."""
        mapping = {
            self.ERROR: 1,
            self.WARNING: 2,
            self.INFO: 3,
            self.HINT: 4,
        }
        return mapping[self]

    @property
    def short(self) -> str:
        """Get single-letter abbreviation."""
        return self.value[0].upper()


# Error handling patterns for consistent returns
def empty_table():
    """Return empty list for table displays when error/no data."""
    return []


def empty_tree():
    """Return empty dict for tree displays when error/no data."""
    return {}
