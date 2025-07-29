#!/usr/bin/env python3
"""
Typer CLI Integration Demo

This example demonstrates how ReplKit2 commands work across three modes:
- REPL: Interactive mode with formatted output
- CLI: Command-line interface via Typer
- MCP: Model Context Protocol server

Run as REPL:
    uv run python examples/typer_demo.py

Run as CLI:
    uv run --extra cli python examples/typer_demo.py --cli list-tasks
    uv run --extra cli python examples/typer_demo.py --cli add "New task"
    uv run --extra cli python examples/typer_demo.py --cli done 1

Run as MCP server:
    uv run --extra mcp python examples/typer_demo.py --mcp
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import json
from replkit2 import App


@dataclass
class TodoState:
    """State for todo application with automatic JSON persistence."""

    todos: list[dict] = field(default_factory=list)
    next_id: int = 1

    def __post_init__(self):
        """Load state from JSON on initialization."""
        # Store in examples/data/ relative to this script
        self._state_file = Path(__file__).parent / "data" / "todo-cli-state.json"
        self._state_file.parent.mkdir(exist_ok=True)  # Ensure directory exists

        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                self.todos = data.get("todos", [])
                self.next_id = data.get("next_id", 1)
            except Exception:
                pass  # Use defaults if file is corrupted

    def save(self):
        """Save state to JSON file."""
        self._state_file.write_text(json.dumps({"todos": self.todos, "next_id": self.next_id}, indent=2))


# Create app with our persistent state class
app = App("todo-cli", TodoState)


@app.command(
    display="table",
    headers=["ID", "Task", "Priority", "Done"],
    typer={
        "help": "List all tasks with optional status filter",
        "epilog": "Filter by status using --done or --pending",
    },
)
def list_tasks(state, done: Optional[bool] = None):
    """List all tasks."""
    todos = state.todos

    # Filter by status if requested
    if done is not None:
        todos = [t for t in todos if t["done"] == done]

    return [
        {"ID": t["id"], "Task": t["task"], "Priority": f"P{t['priority']}", "Done": "[X]" if t["done"] else "[ ]"}
        for t in todos
    ]


@app.command(
    display="box",
    typer={
        "help": "Add a new task to the list",
        "short_help": "Add task",
    },
    fastmcp={"type": "tool", "tags": {"productivity"}},
)
def add(state, task: str, priority: int = 3):
    """Add a new task with priority (1-5)."""
    if not 1 <= priority <= 5:
        return "Priority must be between 1 and 5"

    todo = {"id": state.next_id, "task": task, "priority": priority, "done": False}
    state.todos.append(todo)
    state.next_id += 1
    state.save()  # Persist to JSON

    return f"Added task #{todo['id']}: {task} (Priority {priority})"


@app.command(
    typer={
        "help": "Mark a task as done",
        "rich_help_panel": "Task Management",
    }
)
def done(state, task_id: int):
    """Mark task as completed."""
    for todo in state.todos:
        if todo["id"] == task_id:
            if todo["done"]:
                return f"Task #{task_id} is already done"
            todo["done"] = True
            state.save()  # Persist to JSON
            return f"Completed task #{task_id}: {todo['task']}"

    return f"Task #{task_id} not found"


@app.command(
    display="progress",
    show_percentage=True,
    typer={
        "help": "Show completion progress",
        "rich_help_panel": "Statistics",
    },
)
def progress(state):
    """Show task completion progress."""
    if not state.todos:
        return {"value": 0, "total": 0, "label": "No tasks"}

    done_count = sum(1 for t in state.todos if t["done"])
    return {"value": done_count, "total": len(state.todos), "label": "Completion"}


@app.command(
    display="tree",
    typer={"enabled": False},  # REPL-only command
)
def debug(state):
    """Debug view of state (REPL only)."""
    return {
        "todos": state.todos,
        "stats": {
            "total": len(state.todos),
            "done": sum(1 for t in state.todos if t["done"]),
            "next_id": state.next_id,
        },
    }


@app.command(
    typer={"hidden": True}  # Hidden from CLI help
)
def clear(state):
    """Clear all tasks."""
    count = len(state.todos)
    state.todos.clear()
    state.next_id = 1
    state.save()  # Persist to JSON
    return f"Cleared {count} tasks"


if __name__ == "__main__":
    import sys

    if "--cli" in sys.argv:
        # Run as CLI app
        sys.argv.remove("--cli")
        app.cli()
    elif "--mcp" in sys.argv:
        # Run as MCP server
        app.mcp.run()
    else:
        # Run as REPL
        app.run(title="Todo CLI Demo")
