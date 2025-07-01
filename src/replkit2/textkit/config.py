"""Global configuration for textkit."""

from dataclasses import dataclass


@dataclass
class Config:
    """Global configuration for text display."""

    width: int = 80  # Page width for all displays
    indent: int = 2  # Default indentation spaces
    hr_char: str = "-"  # Character for horizontal rules
    component_spacing: int = 1  # Default lines between components


# Global config instance
config = Config()
