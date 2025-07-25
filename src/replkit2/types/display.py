"""Type-safe display type definitions linking display types to expected data structures."""

from typing import Any, TypeVar, Protocol
from dataclasses import dataclass

# Type variables for generic display data
T = TypeVar("T", covariant=True)


class DisplayData(Protocol[T]):
    """Protocol for display data validation."""

    def validate(self, data: Any) -> T:
        """Validate and convert data to expected type."""
        ...


@dataclass
class TableData:
    """Expected data structure for table display."""

    rows: list[dict[str, Any]] | list[list[Any]]

    @classmethod
    def validate(cls, data: Any) -> "TableData":
        """Validate data is suitable for table display."""
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                return cls(rows=data)
            elif isinstance(data[0], (list, tuple)):
                return cls(rows=data)
        raise ValueError(f"Table display expects list[dict] or list[list], got {type(data)}")


@dataclass
class TreeData:
    """Expected data structure for tree display."""

    root: dict[str, Any]

    @classmethod
    def validate(cls, data: Any) -> "TreeData":
        """Validate data is suitable for tree display."""
        if isinstance(data, dict):
            return cls(root=data)
        raise ValueError(f"Tree display expects dict, got {type(data)}")


@dataclass
class ProgressData:
    """Expected data structure for progress display."""

    value: int | float
    total: int | float | None = None
    label: str = ""

    @classmethod
    def validate(cls, data: Any) -> "ProgressData":
        """Validate data is suitable for progress display."""
        if isinstance(data, dict):
            return cls(value=data.get("value", 0), total=data.get("total"), label=data.get("label", ""))
        elif isinstance(data, (int, float)):
            return cls(value=data)
        raise ValueError(f"Progress display expects dict or number, got {type(data)}")


@dataclass
class BarChartData:
    """Expected data structure for bar chart display."""

    values: dict[str, int | float]

    @classmethod
    def validate(cls, data: Any) -> "BarChartData":
        """Validate data is suitable for bar chart display."""
        if isinstance(data, dict):
            # Check all values are numeric
            for k, v in data.items():
                if not isinstance(v, (int, float)):
                    raise ValueError(f"Bar chart values must be numeric, got {type(v)} for key {k}")
            return cls(values=data)
        raise ValueError(f"Bar chart display expects dict[str, number], got {type(data)}")


# Registry mapping display types to their expected data structures
DISPLAY_TYPES = {
    "table": TableData,
    "tree": TreeData,
    "progress": ProgressData,
    "bar_chart": BarChartData,
    # box and list accept any data converted to string
    "box": None,
    "list": None,
}


def validate_display_data(display_type: str, data: Any) -> Any:
    """Validate data matches expected structure for display type."""
    validator = DISPLAY_TYPES.get(display_type)
    if validator:
        return validator.validate(data)
    return data  # No validation for custom display types
