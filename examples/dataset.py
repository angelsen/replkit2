#!/usr/bin/env python
"""Dataset preview with ExecutionContext.

Demonstrates adaptive command behavior based on execution mode:
- REPL: Compact output for humans
- MCP: Full data for LLM analysis
- CLI: Formatted output for piping
- Programmatic: Structured data for APIs

Key concepts: Context-aware defaults, mode detection, backward compatibility.

Run modes:
    python examples/dataset.py              # REPL mode
    python examples/dataset.py --mcp         # MCP mode
    python examples/dataset.py cli info      # CLI mode
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from replkit2 import App
from replkit2.types import ExecutionContext


@dataclass
class DemoState:
    """Sample state with dataset for demo."""

    data: List[dict] = field(default_factory=lambda: [
        {"id": 1, "name": "Alpha", "value": 100, "priority": "high"},
        {"id": 2, "name": "Beta", "value": 85, "priority": "medium"},
        {"id": 3, "name": "Gamma", "value": 92, "priority": "high"},
        {"id": 4, "name": "Delta", "value": 78, "priority": "low"},
        {"id": 5, "name": "Epsilon", "value": 88, "priority": "medium"},
        {"id": 6, "name": "Zeta", "value": 95, "priority": "high"},
        {"id": 7, "name": "Eta", "value": 82, "priority": "medium"},
        {"id": 8, "name": "Theta", "value": 91, "priority": "high"},
        {"id": 9, "name": "Iota", "value": 76, "priority": "low"},
        {"id": 10, "name": "Kappa", "value": 89, "priority": "medium"},
    ])


# Create app with state
app = App("context-demo", DemoState, mcp_config={"uri_scheme": "demo"})


# Example 1: Context-aware defaults with user override
@app.command(
    display="table",
    headers=["ID", "Name", "Value", "Priority"],
    fastmcp={"type": "tool"}
)
def preview(state, limit: int = None, _ctx: ExecutionContext = None):
    """Preview dataset with context-aware row limit.

    Args:
        limit: Max rows to show (default: 3 for REPL, all for MCP/CLI/programmatic)
        _ctx: Execution context (auto-injected)

    Pattern: Smart defaults based on mode, but user can always override.

    Examples:
        # REPL: Shows 3 rows by default (compact)
        >>> preview()

        # REPL: User override shows all
        >>> preview(limit=None)

        # MCP: Shows all rows by default (full data for LLM)
        # CLI: Shows all rows by default
    """
    # Context-aware default
    if limit is None:
        # REPL: compact output for terminal viewing
        # Others: full data for analysis/processing
        limit = 3 if _ctx and _ctx.is_repl() else None

    data = state.data[:limit] if limit else state.data

    return [
        {"ID": d["id"], "Name": d["name"], "Value": d["value"], "Priority": d["priority"]}
        for d in data
    ]


# Example 2: Different data structures per mode
@app.command(fastmcp={"type": "tool"})
def analyze(state, _ctx: ExecutionContext = None):
    """Return different data structure based on execution mode.

    Pattern: Commands decide what data to return based on context.

    Returns:
        - REPL: Simple summary string (human-readable)
        - MCP: Structured dict with full stats (LLM-friendly)
        - CLI/programmatic: Balanced structured data
    """
    data = state.data
    total = len(data)
    avg_value = sum(d["value"] for d in data) / total
    high_priority = sum(1 for d in data if d["priority"] == "high")

    if _ctx and _ctx.is_repl():
        # REPL: Simple string for human viewing
        return f"Dataset: {total} items, avg value: {avg_value:.1f}, {high_priority} high priority"

    elif _ctx and _ctx.is_mcp():
        # MCP: Rich structured data for LLM analysis
        return {
            "summary": {
                "total_items": total,
                "average_value": round(avg_value, 2),
                "high_priority_count": high_priority,
                "high_priority_percentage": round(high_priority / total * 100, 1)
            },
            "by_priority": {
                "high": [d for d in data if d["priority"] == "high"],
                "medium": [d for d in data if d["priority"] == "medium"],
                "low": [d for d in data if d["priority"] == "low"]
            },
            "statistics": {
                "min_value": min(d["value"] for d in data),
                "max_value": max(d["value"] for d in data),
                "median_value": sorted(d["value"] for d in data)[total // 2]
            }
        }

    else:
        # CLI/programmatic: Balanced structure
        return {
            "total_items": total,
            "average_value": round(avg_value, 2),
            "high_priority_count": high_priority,
            "priority_distribution": {
                "high": sum(1 for d in data if d["priority"] == "high"),
                "medium": sum(1 for d in data if d["priority"] == "medium"),
                "low": sum(1 for d in data if d["priority"] == "low")
            }
        }


# Example 3: Mode detection for debugging/logging
@app.command(display="box", fastmcp={"type": "tool"})
def info(state, _ctx: ExecutionContext = None):
    """Show execution context information.

    Pattern: Inspect context to understand execution environment.

    Demonstrates:
    - Mode detection (is_repl, is_mcp, is_cli, is_programmatic)
    - Transport type access
    - Metadata inspection (for MCP)
    """
    if _ctx is None:
        return "No context available (this shouldn't happen!)"

    # Detect mode
    mode_info = []
    if _ctx.is_repl():
        mode_info.append("Running in REPL mode (interactive Python shell)")
    elif _ctx.is_mcp():
        mode_info.append("Running in MCP mode (Model Context Protocol)")
    elif _ctx.is_cli():
        mode_info.append("Running in CLI mode (command-line interface)")
    elif _ctx.is_programmatic():
        mode_info.append("Running in programmatic mode (app.execute())")

    # Transport type
    mode_info.append(f"Transport: {_ctx.transport.value}")

    # MCP-specific metadata
    if _ctx.is_mcp():
        component_type = _ctx.get_component_type()
        mime_type = _ctx.get_mime_type()
        mode_info.append(f"MCP component type: {component_type or 'not set'}")
        mode_info.append(f"MCP MIME type: {mime_type or 'not set'}")

    return "\n".join(mode_info)


# Example 4: Command without context (backward compatibility)
@app.command(display="table", headers=["ID", "Name", "Value"])
def list_all(state):
    """List all items - no context parameter.

    Pattern: Existing commands without _ctx work unchanged.

    Demonstrates backward compatibility - commands don't need to opt-in
    to context if they don't need adaptive behavior.
    """
    return [{"ID": d["id"], "Name": d["name"], "Value": d["value"]} for d in state.data]


# Example 5: Optional filtering with context-aware defaults
@app.command(
    display="table",
    headers=["ID", "Name", "Value", "Priority"],
    fastmcp={"type": "tool"}
)
def filter_priority(state, priority: str = None, limit: int = None, _ctx: ExecutionContext = None):
    """Filter by priority with context-aware defaults.

    Args:
        priority: Priority level to filter (default: "high" for REPL, all for MCP)
        limit: Max rows (default: 5 for REPL, all for others)
        _ctx: Execution context

    Pattern: Multiple context-aware defaults that work together.
    """
    # Context-aware default for priority filter
    if priority is None:
        # REPL: Default to high priority (most important for quick view)
        # Others: Show all (no filter)
        priority = "high" if _ctx and _ctx.is_repl() else None

    # Filter data
    if priority:
        filtered = [d for d in state.data if d["priority"] == priority]
    else:
        filtered = state.data

    # Context-aware default for limit
    if limit is None:
        limit = 5 if _ctx and _ctx.is_repl() else None

    # Apply limit
    result = filtered[:limit] if limit else filtered

    return [
        {"ID": d["id"], "Name": d["name"], "Value": d["value"], "Priority": d["priority"]}
        for d in result
    ]


# Example 6: Explicit context passing in programmatic mode
@app.command(display="box")
def programmatic_demo(state):
    """Demonstrate explicit context passing.

    This command shows how to pass context explicitly when calling
    other commands programmatically. Not exposed via MCP.
    """
    from replkit2.types import ExecutionContext

    # Call analyze with explicit REPL context
    repl_ctx = ExecutionContext.for_repl()
    repl_result = app.execute("analyze", _ctx=repl_ctx)

    # Call analyze with explicit MCP context
    mcp_ctx = ExecutionContext.for_mcp(component_type="tool")
    mcp_result = app.execute("analyze", _ctx=mcp_ctx)

    return f"REPL result: {repl_result}\n\nMCP result: {mcp_result}"


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        # MCP mode
        app.mcp.run()
    else:
        # REPL mode
        print("=" * 70)
        print("ExecutionContext Demo - ReplKit2")
        print("=" * 70)
        print("\nTry these commands:")
        print("  info()              - Show execution context info")
        print("  preview()           - Preview with context-aware limit (3 rows)")
        print("  preview(limit=10)   - Override default limit")
        print("  analyze()           - Different output per mode")
        print("  list_all()          - Command without context (backward compat)")
        print("  filter_priority()   - Multiple context-aware defaults")
        print("  help()              - Show all commands")
        print("\nContext-aware behavior:")
        print("  - REPL: Compact output (fewer rows, simpler format)")
        print("  - MCP: Full data (all rows, structured for LLM)")
        print("  - User can always override with explicit parameters")
        print("=" * 70)
        print()

        app.run(title="Context Demo")
