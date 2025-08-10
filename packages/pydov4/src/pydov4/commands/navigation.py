"""Navigation commands for PyDoV4 v3."""

from typing import Optional, Union

from ..app import app
from ..constants import empty_table


@app.command(display="box", title="Hover Information")
def hover(state, line: int, column: Optional[int] = None):
    """Get hover information at a position.

    Args:
        line: Line number (1-indexed)
        column: Column number (0-indexed, auto-detected if not provided)
    """
    if not state.client.client:
        return "Error: Not connected"

    if not state.current_file:
        return "Error: No file is currently open"

    if not state.client.server_capabilities.hover_provider:
        return "Server does not support hover"

    file_path = state.open_files.get(state.current_file)
    if not file_path or not file_path.exists():
        return "Error: Current file not found"

    lines = file_path.read_text().splitlines()
    if not 1 <= line <= len(lines):
        return f"Error: Line {line} out of range (file has {len(lines)} lines)"

    # Auto-detect column if not provided
    if column is None:
        line_text = lines[line - 1]
        column = len(line_text) - len(line_text.lstrip())

    try:
        result = state.client.hover(state.current_file, line, column)

        if not result:
            return f"No hover information at line {line}, column {column}"

        # Extract hover content
        if hasattr(result, "contents"):
            if isinstance(result.contents, str):
                return result.contents
            elif hasattr(result.contents, "value"):
                return result.contents.value
            else:
                return str(result.contents)

        return "Hover information available but format unknown"

    except Exception as e:
        return f"Error getting hover info: {e}"


@app.command(display="box", title="Navigation")
def goto(state, target: Union[int, str]):
    """Go to a line number or symbol.

    Args:
        target: Line number or "type:name" pattern
               Examples: 42, "def:main", "class:MyClass"
    """
    if not state.current_file:
        return "Error: No file is currently open"

    file_path = state.open_files.get(state.current_file)
    if not file_path or not file_path.exists():
        return "Error: Current file not found"

    lines = file_path.read_text().splitlines()

    # Handle line number
    if isinstance(target, int):
        if 1 <= target <= len(lines):
            return f"Line {target}: {lines[target - 1]}"
        else:
            return f"Error: Line {target} out of range (file has {len(lines)} lines)"

    # Handle symbol search
    if isinstance(target, str) and ":" in target:
        symbol_type, symbol_name = target.split(":", 1)

        patterns = {
            "def": rf"^\s*def\s+{symbol_name}\s*\(",
            "class": rf"^\s*class\s+{symbol_name}\s*[\(:]",
            "async": rf"^\s*async\s+def\s+{symbol_name}\s*\(",
        }

        pattern = patterns.get(symbol_type.lower())
        if not pattern:
            return f"Unknown symbol type: {symbol_type}. Use 'def', 'class', or 'async'"

        import re

        for i, line_text in enumerate(lines, 1):
            if re.match(pattern, line_text):
                return f"Line {i}: {line_text.strip()}"

        return f"Symbol not found: {target}"

    return "Invalid target. Use line number or 'type:name' pattern"


@app.command(display="table", headers=["Type", "Name", "Location", "Kind"])
def find(state, query: str, type: str = "symbol"):
    """Find symbols or references.

    Args:
        query: Search query
        type: Search type - 'symbol' or 'references'
    """
    if not state.client.client or not state.current_file:
        return empty_table()

    if type == "symbol" and state.client.server_capabilities.document_symbol_provider:
        try:
            symbols = state.client.document_symbols(state.current_file)

            results = []
            for symbol in symbols:
                if query.lower() in symbol.name.lower():
                    results.append(
                        {
                            "Type": "symbol",
                            "Name": symbol.name,
                            "Location": f"line {symbol.location.range.start.line + 1}",
                            "Kind": getattr(symbol.kind, "name", str(symbol.kind)),
                        }
                    )

            return results

        except Exception:
            return empty_table()

    return empty_table()


@app.command(display="table", headers=["File", "Line", "Text"])
def definition(state, line: int, column: Optional[int] = None):
    """Go to definition of symbol at position.

    Args:
        line: Line number (1-indexed)
        column: Column number (0-indexed)
    """
    if not state.client.client or not state.current_file:
        return empty_table()

    if not state.client.server_capabilities.definition_provider:
        return empty_table()

    # Auto-detect column
    if column is None:
        file_path = state.open_files.get(state.current_file)
        if file_path and file_path.exists():
            lines = file_path.read_text().splitlines()
            if 1 <= line <= len(lines):
                line_text = lines[line - 1]
                column = len(line_text) - len(line_text.lstrip())

    try:
        locations = state.client.definition(state.current_file, line, column or 0)

        if not locations:
            return empty_table()

        if not isinstance(locations, list):
            locations = [locations]

        results = []
        for loc in locations:
            # Find file path for URI
            file_path = None
            for uri, path in state.open_files.items():
                if uri == loc.uri:
                    file_path = path
                    break

            # Get line content
            text = "<file not open>"
            if file_path:
                try:
                    lines = file_path.read_text().splitlines()
                    line_num = loc.range.start.line
                    if 0 <= line_num < len(lines):
                        text = lines[line_num].strip()
                        if len(text) > 60:
                            text = text[:60] + "..."
                except Exception:
                    text = "<error reading file>"

            results.append(
                {
                    "File": file_path.name if file_path else loc.uri,
                    "Line": str(loc.range.start.line + 1),
                    "Text": text,
                }
            )

        return results

    except Exception:
        return empty_table()
