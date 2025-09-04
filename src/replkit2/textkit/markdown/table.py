"""Markdown table element with truncation and transform support."""

from .base import MarkdownElement
from .transforms import apply_transform


class Table(MarkdownElement):
    """Markdown table with proper formatting, truncation, and transforms.

    Creates properly formatted markdown tables with configurable alignment,
    automatic column width calculation, and per-column data transformation.
    """

    element_type = "table"
    supports_truncation = True  # This element supports truncation
    supports_transforms = True   # This element supports transforms

    def __init__(
        self,
        headers: list[str],
        rows: list[dict],
        align: str = "left",
        truncate: dict[str, dict] | None = None,
        transforms: dict[str, str] | None = None,
    ):
        """Initialize table with headers, data, and display options.

        Args:
            headers: List of column header names.
            rows: List of dictionaries with data for each row (full data).
            align: Column alignment (left/right/center). Defaults to "left".
            truncate: Per-column truncation config.
                Example: {"URL": {"max": 60, "mode": "middle"}}
            transforms: Per-column transform functions.
                Example: {"Size": "format_size", "Time": "format_timestamp"}
        """
        self.headers = headers
        self.rows = rows
        self.align = align
        self.truncate = truncate or {}
        self.transforms = transforms or {}

    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        """Create Table instance from dictionary data."""
        return cls(
            headers=data.get("headers", []),
            rows=data.get("rows", []),
            align=data.get("align", "left"),
            truncate=data.get("truncate", {}),
            transforms=data.get("transforms", {}),
        )

    def render(self) -> str:
        """Render table as markdown text with proper formatting.

        Applies transforms and truncation during rendering,
        preserving full data in self.rows.
        """
        if not self.headers:
            return ""

        # Process rows with transforms and truncation
        processed_rows = self._process_rows()

        # Calculate maximum width for each column
        col_widths = self._calculate_column_widths(processed_rows)

        lines = []

        # Header with padding
        padded_headers = self._pad_values(self.headers, col_widths)
        lines.append("| " + " | ".join(padded_headers) + " |")

        # Separator with proper width
        sep = self._create_separator(col_widths)
        lines.append("|" + "|".join(sep) + "|")

        # Rows with padding
        for row in processed_rows:
            padded_values = []
            for header, width in zip(self.headers, col_widths):
                value = str(row.get(header, ""))
                padded_values.append(self._pad_value(value, width))
            lines.append("| " + " | ".join(padded_values) + " |")

        return "\n".join(lines)

    def _process_rows(self) -> list[dict]:
        """Process rows with transforms and truncation."""
        processed = []

        for row in self.rows:
            processed_row = {}

            for header in self.headers:
                value = row.get(header, "")

                # Apply transform if specified
                if header in self.transforms:
                    transform_name = self.transforms[header]
                    value = apply_transform(value, transform_name)

                # Apply truncation if specified
                if header in self.truncate:
                    config = self.truncate[header]
                    value = self._truncate_value(str(value), config)
                else:
                    value = str(value)

                processed_row[header] = value

            processed.append(processed_row)

        return processed

    def _calculate_column_widths(self, processed_rows: list[dict]) -> list[int]:
        """Calculate maximum width for each column."""
        col_widths = []

        for header in self.headers:
            # Start with header width
            max_width = len(header)

            # Check all row values for this column
            for row in processed_rows:
                value = str(row.get(header, ""))
                max_width = max(max_width, len(value))

            col_widths.append(max_width)

        return col_widths

    def _pad_value(self, value: str, width: int) -> str:
        """Pad a value based on alignment."""
        if self.align == "right":
            return value.rjust(width)
        elif self.align == "center":
            return value.center(width)
        else:  # left
            return value.ljust(width)

    def _pad_values(self, values: list[str], widths: list[int]) -> list[str]:
        """Pad multiple values based on alignment."""
        return [self._pad_value(val, width) for val, width in zip(values, widths)]

    def _create_separator(self, widths: list[int]) -> list[str]:
        """Create separator line based on alignment."""
        sep = []
        for width in widths:
            if self.align == "right":
                sep.append("-" * (width + 1) + ":")
            elif self.align == "center":
                sep.append(":" + "-" * width + ":")
            else:  # left
                sep.append(":" + "-" * (width + 1))
        return sep
