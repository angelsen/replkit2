"""Example showing proper custom formatter implementation with ReplKit2 0.2.0+"""

from dataclasses import dataclass, field
from replkit2 import App
from replkit2.types.core import CommandMeta
from replkit2.textkit import box, compose


@dataclass
class DemoState:
    sessions: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


app = App("formatter-demo", DemoState)


# Custom formatter that properly uses the formatter parameter
@app.formatter.register("dashboard")
def dashboard_display(data, meta, formatter):
    """
    Dashboard display showing how to compose formatters.

    Demonstrates:
    1. Using formatter for data transformation (list[dict] → table)
    2. Direct textkit usage for layout (box, compose)
    3. Mixing both approaches for maximum flexibility
    """
    sections = []

    # Section 1: Active Sessions (using formatter for conversion)
    if "sessions" in data and data["sessions"]:
        # Use formatter to handle dict→list conversion
        session_meta = CommandMeta(
            display="table", display_opts={"headers": ["Session ID", "User", "Status", "Duration"]}
        )
        session_table = formatter.format(data["sessions"], session_meta)
        sections.append(box(session_table, title="Active Sessions"))

    # Section 2: Statistics (using formatter for bar chart)
    if "stats" in data and data["stats"]:
        stats_meta = CommandMeta(display="bar_chart", display_opts={"show_values": True, "width": 60})
        stats_chart = formatter.format(data["stats"], stats_meta)
        sections.append(box(stats_chart, title="Resource Usage"))

    # Section 3: Summary (direct string formatting)
    if "summary" in data:
        sections.append(box(data["summary"], title="System Status"))

    # Compose all sections with spacing
    return compose(*sections, spacing=1)


# Commands that return data for the dashboard
@app.command
def add_session(state, session_id: str, user: str, status: str = "active"):
    """Add a test session."""
    state.sessions.append({"Session ID": session_id, "User": user, "Status": status, "Duration": "5m 23s"})
    state.stats = {"CPU": 45, "Memory": 72, "Disk": 38, "Network": 15}
    return f"Added session: {session_id}"


@app.command(display="dashboard")
def status(state):
    """Show system dashboard."""
    active_count = sum(1 for s in state.sessions if s["Status"] == "active")

    return {
        "sessions": state.sessions,
        "stats": state.stats,
        "summary": f"Total Sessions: {len(state.sessions)}\nActive: {active_count}\nSystem: Healthy",
    }


# Example showing direct textkit usage vs formatter usage
@app.command(display="custom:comparison")
def show_comparison(state):
    """Show the difference between direct textkit and formatter usage."""
    test_data = [{"Name": "Alice", "Score": 95}, {"Name": "Bob", "Score": 87}]
    return test_data


@app.formatter.register("custom:comparison")
def comparison_display(data, meta, formatter):
    """Shows both approaches side by side."""
    from replkit2.textkit import table, compose

    # Approach 1: Direct textkit (manual conversion)
    rows = [[d["Name"], str(d["Score"])] for d in data]
    direct_table = table(rows, headers=["Name", "Score"])
    direct_box = box(direct_table, title="Direct TextKit (Manual)")

    # Approach 2: Using formatter (automatic conversion)
    table_meta = CommandMeta(display="table", display_opts={"headers": ["Name", "Score"]})
    formatter_table = formatter.format(data, table_meta)
    formatter_box = box(formatter_table, title="Via Formatter (Automatic)")

    return compose("Both approaches produce identical output:", "", direct_box, formatter_box, spacing=1)


if __name__ == "__main__":
    app.run()
