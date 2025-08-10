"""Core commands for PyDoV4 v3 - connection and status."""

from ..app import app
from ..constants import Severity


@app.command(display="box", title="Server Connected")
def connect(state, server: str = "basedpyright"):
    """Connect to an LSP server.

    Args:
        server: Server name (basedpyright, pyright, ruff, pylsp)
    """
    try:
        result = state.client.connect(server)

        lines = [f"Connected to {result['name']} v{result['version']}"]

        # Show key features if available
        if "capabilities" in result:
            caps = result["capabilities"]
            features = []

            if caps.get("hover") or caps.get("definition"):
                features.append("navigation")
            if caps.get("diagnostics"):
                features.append("diagnostics")
            if caps.get("code_action"):
                features.append("fixes")
            if caps.get("completion"):
                features.append("completion")
            if caps.get("formatting"):
                features.append("formatting")

            if features:
                lines.append(f"Features: {', '.join(features)}")

        return "\n".join(lines)

    except Exception as e:
        return f"Failed to connect: {e}"


@app.command(display="box", title="Disconnected")
def disconnect(state):
    """Disconnect from the LSP server."""
    if not state.client.client:
        return "Not connected to any server"

    state.client.disconnect()
    state.current_file = None
    state.open_files.clear()

    return "Disconnected from LSP server"


@app.command(display="box", title="Status")
def status(state, verbose: bool = False):
    """Show connection status and workspace info.

    Args:
        verbose: Show detailed capabilities
    """
    lines = []

    if not state.client.client:
        lines.append("[X] Not connected")
        lines.append("")
        lines.append("Use connect() to connect to a language server")
        return "\n".join(lines)

    lines.append("[OK] Connected to LSP server")
    lines.append(f"[Files: {len(state.open_files)}]")

    if state.current_file:
        current_path = state.open_files.get(state.current_file)
        if current_path:
            lines.append(f"[Current: {current_path.name}]")

    # Diagnostic summary
    total_diags = sum(len(diags) for diags in state.client.diagnostics.values())
    if total_diags > 0:
        # Count by severity
        counts = {"error": 0, "warning": 0, "info": 0, "hint": 0}
        for diags in state.client.diagnostics.values():
            for d in diags:
                severity = Severity.from_lsp(d.severity)
                counts[severity.value] += 1

        # Build summary
        parts = []
        if counts["error"] > 0:
            parts.append(f"{counts['error']} errors")
        if counts["warning"] > 0:
            parts.append(f"{counts['warning']} warnings")

        lines.append(f"[!] Diagnostics: {', '.join(parts)}" if parts else "[i] Info/hints only")
    else:
        lines.append("[+] No diagnostics")

    if verbose and state.client.server_capabilities:
        lines.append("")
        lines.append("Capabilities:")

        caps = state.client._summarize_capabilities(state.client.server_capabilities)
        for feature, supported in sorted(caps.items()):
            symbol = "+" if supported else "-"
            lines.append(f"  {symbol} {feature}")

    return "\n".join(lines)


@app.command(display="box", title="Demo")
def demo(state):
    """Show quick demo commands."""
    return """PyDoV4 Demo Commands:

1. connect()                  # Connect to basedpyright
2. open('test.py')            # Open test file
3. diagnostics()              # Show issues
4. view_diagnostics()         # Show code with diagnostics
5. goto(10)                   # Navigate to line 10
6. hover(10, 5)               # Get hover info

Use help() to see all available commands."""
