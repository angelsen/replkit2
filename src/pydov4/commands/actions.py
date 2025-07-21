"""Code actions commands for PyDoV4 v3."""

from typing import Optional

from ..app import app
from ..constants import empty_table, empty_tree


# Store actions for apply command
_last_actions = []


@app.command(display="table", headers=["#", "Title", "Kind", "Diagnostic"])
def actions(state, line: Optional[int] = None, column: Optional[int] = None):
    """List available code actions at position or for the whole file.

    Args:
        line: Line number (1-indexed), or None for whole file
        column: Column number (0-indexed)
    """
    global _last_actions

    if not state.client.client or not state.current_file:
        return empty_table()

    if not state.client.server_capabilities.code_action_provider:
        return empty_table()

    try:
        # Get code actions
        if line is not None:
            actions = state.client.code_actions(state.current_file, line, column or 0)
        else:
            actions = state.client.code_actions(state.current_file, 1, 0)

        if not actions:
            return empty_table()

        # Store for apply command
        _last_actions = actions

        # Convert to clean Python data
        results = []
        for i, action in enumerate(actions, 1):
            title = action.title if hasattr(action, "title") else str(action)

            # Extract kind
            kind = "-"
            if hasattr(action, "kind"):
                if hasattr(action.kind, "value"):
                    kind = action.kind.value.split(".")[-1]
                else:
                    kind = str(action.kind)

            # Extract related diagnostic
            diagnostic = "-"
            if hasattr(action, "diagnostics") and action.diagnostics:
                diag = action.diagnostics[0]
                if hasattr(diag, "message"):
                    msg = diag.message
                    diagnostic = msg[:40] + "..." if len(msg) > 40 else msg

            results.append(
                {
                    "#": str(i),
                    "Title": title,
                    "Kind": kind,
                    "Diagnostic": diagnostic,
                }
            )

        return results

    except Exception:
        return empty_table()


@app.command(display="box", title="Action Applied")
def apply(state, number: int):
    """Apply a code action by number from the last actions() call.

    Args:
        number: Action number to apply (1-based)
    """
    global _last_actions

    if not state.client.client:
        return "Error: Not connected"

    if not _last_actions:
        return "Error: No actions available. Run actions() first."

    if not 1 <= number <= len(_last_actions):
        return f"Error: Invalid action number. Choose 1-{len(_last_actions)}"

    action = _last_actions[number - 1]

    try:
        state.client.apply_action(action)
        _last_actions = []

        title = action.title if hasattr(action, "title") else "Action"
        return f"Applied: {title}"

    except Exception as e:
        return f"Error applying action: {e}"


@app.command(display="tree")
def actions_by_kind(state):
    """Show code actions organized by kind."""
    if not state.client.client or not state.current_file:
        return empty_tree()

    try:
        actions = state.client.code_actions(state.current_file, 1, 0)

        if not actions:
            return {"No actions available": []}

        # Organize by kind
        by_kind = {}
        for action in actions:
            kind = "Other"
            if hasattr(action, "kind") and action.kind:
                if hasattr(action.kind, "value"):
                    kind = action.kind.value.split(".")[-1]
                else:
                    kind = str(action.kind)

            if kind not in by_kind:
                by_kind[kind] = []

            title = action.title if hasattr(action, "title") else str(action)
            by_kind[kind].append(title)

        return by_kind

    except Exception:
        return {"Error": ["Could not retrieve actions"]}
