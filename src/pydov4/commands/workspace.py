"""Workspace commands for PyDoV4 v3 - file management and editing."""

import re
from pathlib import Path
from typing import Optional

from ..app import app
from ..constants import empty_table


@app.command(display="box", title="File Opened")
def open(state, path: str, goto_line: Optional[int] = None):
    """Open a file for LSP operations.

    Args:
        path: Path to the file to open
        goto_line: Optional line number to jump to
    """
    if not state.client.client:
        return "Error: Not connected. Use connect() first."

    file_path = Path(path)
    if not file_path.exists():
        return f"Error: File not found: {path}"

    if not file_path.is_file():
        return f"Error: Not a file: {path}"

    try:
        uri = state.client.open_document(file_path)
        state.current_file = uri
        state.open_files[uri] = file_path

        lines = file_path.read_text().splitlines()

        result = [
            f"Opened: {file_path.name}",
            f"Path: {file_path}",
            f"Lines: {len(lines)}",
        ]

        # Count diagnostics
        diag_count = len(state.client.diagnostics.get(uri, []))
        if diag_count > 0:
            result.append(f"Diagnostics: {diag_count}")

        # Show requested line
        if goto_line and 1 <= goto_line <= len(lines):
            result.append("")
            result.append(f"Line {goto_line}: {lines[goto_line - 1]}")

        return "\n".join(result)

    except Exception as e:
        return f"Error opening file: {e}"


@app.command(display="box", title="File Closed")
def close(state, path: Optional[str] = None):
    """Close a file and stop LSP tracking.

    Args:
        path: Path to close (current file if not specified)
    """
    if not state.client.client:
        return "Error: Not connected"

    if path is None:
        if not state.current_file:
            return "Error: No file is currently open"
        uri = state.current_file
        file_path = state.open_files.get(uri)
    else:
        # Find URI for the given path
        file_path = Path(path)
        uri = None
        for u, p in state.open_files.items():
            if p == file_path:
                uri = u
                break

        if not uri:
            return f"Error: File not open: {path}"

    state.client.close_document(uri)
    del state.open_files[uri]

    if state.current_file == uri:
        state.current_file = next(iter(state.open_files.keys()), None)

    return f"Closed: {file_path.name if file_path else uri}"


@app.command(display="table", headers=["File", "Path", "Issues", "Current"])
def files(state):
    """List open files with diagnostic counts."""
    if not state.open_files:
        return empty_table()

    results = []
    for uri, path in state.open_files.items():
        diag_count = len(state.client.diagnostics.get(uri, []))

        results.append(
            {
                "File": path.name,
                "Path": str(path.parent),
                "Issues": str(diag_count) if diag_count > 0 else "-",
                "Current": "*" if uri == state.current_file else "",
            }
        )

    return sorted(results, key=lambda x: x["File"])


@app.command(display="box", title="File View")
def view(state, start_line: int = 1, count: int = 20):
    """View current file content.

    Args:
        start_line: Starting line number (1-indexed)
        count: Number of lines to display
    """
    if not state.current_file:
        return "No file is currently open"

    file_path = state.open_files.get(state.current_file)
    if not file_path or not file_path.exists():
        return "Current file not found"

    try:
        lines = file_path.read_text().splitlines()
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + count)

        # Format lines with line numbers
        result = []
        for i in range(start_idx, end_idx):
            result.append(f"{i + 1:4d} | {lines[i]}")

        return "\n".join(result) if result else "Empty file"

    except Exception as e:
        return f"Error reading file: {e}"


@app.command(display="box", title="Edit Result")
def edit(state, line: int, content: str):
    """Replace a line in the current file.

    Args:
        line: Line number to replace (1-indexed)
        content: New content for the line
    """
    if not state.current_file:
        return "Error: No file is currently open"

    file_path = state.open_files.get(state.current_file)
    if not file_path:
        return "Error: Current file not found"

    try:
        lines = file_path.read_text().splitlines()

        if not 1 <= line <= len(lines):
            return f"Error: Line {line} out of range (file has {len(lines)} lines)"

        old_content = lines[line - 1]
        lines[line - 1] = content

        # Write back
        new_text = "\n".join(lines) + "\n"
        file_path.write_text(new_text)

        # Update LSP
        state.client.update_document(state.current_file, new_text)

        return f"Line {line} updated:\n  Old: {old_content}\n  New: {content}"

    except Exception as e:
        return f"Error editing file: {e}"


@app.command(display="box", title="Replace Result")
def replace(state, pattern: str, replacement: str, line: Optional[int] = None):
    """Replace text using regex pattern.

    Args:
        pattern: Regex pattern to match
        replacement: Replacement text
        line: Optional line number to limit replacement
    """
    if not state.current_file:
        return "Error: No file is currently open"

    file_path = state.open_files.get(state.current_file)
    if not file_path:
        return "Error: Current file not found"

    try:
        content = file_path.read_text()
        lines = content.splitlines()

        if line is not None:
            if not 1 <= line <= len(lines):
                return f"Error: Line {line} out of range"

            old_line = lines[line - 1]
            new_line = re.sub(pattern, replacement, old_line)

            if old_line == new_line:
                return f"No matches found on line {line}"

            lines[line - 1] = new_line
            count = 1
        else:
            # Replace in entire file
            new_content = re.sub(pattern, replacement, content)
            if new_content == content:
                return "No matches found"

            lines = new_content.splitlines()
            count = len(re.findall(pattern, content))

        # Write and update
        new_content = "\n".join(lines) + "\n"
        file_path.write_text(new_content)
        state.client.update_document(state.current_file, new_content)

        return f"Replaced {count} occurrence(s)"

    except re.error as e:
        return f"Invalid regex pattern: {e}"
    except Exception as e:
        return f"Error replacing text: {e}"


@app.command(display="box", title="Save Result")
def save(state):
    """Save current file (triggers diagnostic refresh)."""
    if not state.current_file:
        return "Error: No file is currently open"

    file_path = state.open_files.get(state.current_file)
    if file_path and file_path.exists():
        content = file_path.read_text()
        state.client.update_document(state.current_file, content)
        return f"Saved and refreshed: {file_path.name}"

    return "File saved"


@app.command(display="box", title="Refresh Result")
def refresh(state):
    """Refresh diagnostics for all open files."""
    if not state.client.client:
        return "Error: Not connected"

    if not state.open_files:
        return "No files open"

    refreshed = []
    for uri, path in state.open_files.items():
        if path.exists():
            content = path.read_text()
            state.client.update_document(uri, content)
            refreshed.append(path.name)

    return f"Refreshed {len(refreshed)} file(s): {', '.join(refreshed)}"
