"""Diagnostics commands for PyDoV4 v3."""

from typing import Optional

from ..app import app
from ..constants import Severity, empty_table


@app.command(display="table", headers=["File", "Line", "Severity", "Message", "Source"])
def diagnostics(state, severity: Optional[str] = None, path: Optional[str] = None):
    """Show diagnostics for open files.

    Args:
        severity: Filter by severity (error, warning, info, hint)
        path: Filter by file path (partial match)
    """
    if not state.client.client:
        return empty_table()

    results = []

    for uri, diags in state.client.diagnostics.items():
        file_path = state.open_files.get(uri)
        if not file_path:
            continue

        # Apply path filter
        if path and path not in str(file_path):
            continue

        for diag in diags:
            # Convert numeric severity to enum
            diag_severity = Severity.from_lsp(diag.severity)

            # Apply severity filter
            if severity and severity.lower() != diag_severity.value:
                continue

            # Build clean Python dict
            results.append(
                {
                    "File": file_path.name,
                    "Line": str(diag.range.start.line + 1),
                    "Severity": diag_severity.value,
                    "Message": diag.message[:50] + "..." if len(diag.message) > 50 else diag.message,
                    "Source": diag.source or "-",
                }
            )

    return results


@app.command(display="custom:code_diagnostics")
def view_diagnostics(state, start_line: int = 1, count: int = 20):
    """View current file with inline diagnostics.

    Custom display that shows code with diagnostic indicators.

    Args:
        start_line: Starting line number (1-indexed)
        count: Number of lines to display
    """
    if not state.current_file:
        return {"error": "No file open"}

    file_path = state.open_files.get(state.current_file)
    if not file_path or not file_path.exists():
        return {"error": "Current file not found"}

    try:
        lines = file_path.read_text().splitlines()
        diagnostics = state.client.diagnostics.get(state.current_file, [])

        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + count)

        # Build diagnostic map by line number
        diag_by_line = {}
        for diag in diagnostics:
            line_num = diag.range.start.line
            if start_idx <= line_num < end_idx:
                severity = Severity.from_lsp(diag.severity)
                if line_num not in diag_by_line:
                    diag_by_line[line_num] = []
                diag_by_line[line_num].append(
                    {
                        "severity": severity.value,
                        "short": severity.short,
                        "message": diag.message,
                        "source": diag.source,
                    }
                )

        return {
            "file_path": str(file_path),
            "start_line": start_idx + 1,
            "end_line": end_idx,
            "lines": lines[start_idx:end_idx],
            "diagnostics": diag_by_line,
        }

    except Exception as e:
        return {"error": f"Error reading file: {e}"}
