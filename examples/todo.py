#!/usr/bin/env python3
"""
Flask-style Todo App Example

This example demonstrates the modern ReplKit2 patterns:
- Flask-style command decorators with @app.command()
- State as a dataclass passed to commands
- Clean separation of state and behavior
- Multiple display formats (table, box, tree, etc.)

Run:
    uv run python examples/todo.py

Then use:
    >>> todos()         # List all todos
    >>> add("Task")     # Add a new todo
    >>> done(1)         # Mark todo #1 as done
    >>> remove(1)       # Remove todo #1
    >>> stats()         # Show statistics
    >>> report()        # Full report
"""

from dataclasses import dataclass, field
from datetime import datetime
from replkit2 import App
from replkit2.types.core import CommandMeta
from replkit2.textkit import compose, box


@dataclass
class TodoState:
    """State container for the todo application."""

    todos: list[dict] = field(default_factory=list)
    next_id: int = 1
    created_at: datetime = field(default_factory=datetime.now)


# Create the app with state
app = App("todo", TodoState)


# Register custom report display handler
@app.formatter.register("report")
def handle_report(data, meta, formatter):
    """Handle multi-section report display."""
    sections = []
    for title, section_data, opts in data:
        section_meta = CommandMeta(display=opts.get("display"), display_opts=opts)
        formatted = formatter.format(section_data, section_meta)
        if opts.get("box", True):
            sections.append(box(formatted, title=title))
        else:
            sections.append(formatted)
    return compose(*sections, spacing=1)


@app.command(display="table", headers=["ID", "Task", "Priority", "Done", "Created"])
def todos(state):
    """List all todos in a table."""
    if not state.todos:
        return []

    return [
        {
            "ID": t["id"],
            "Task": t["task"][:40] + "..." if len(t["task"]) > 40 else t["task"],
            "Priority": t.get("priority", "medium"),
            "Done": "[X]" if t["done"] else "[ ]",
            "Created": t["created"].strftime("%Y-%m-%d"),
        }
        for t in state.todos
    ]


@app.command()
def add(state, task: str, priority: str = "medium"):
    """Add a new todo task.

    Args:
        task: Description of the task
        priority: Priority level (low, medium, high)
    """
    if priority not in ["low", "medium", "high"]:
        return f"Invalid priority '{priority}'. Use: low, medium, high"

    todo = {"id": state.next_id, "task": task, "priority": priority, "done": False, "created": datetime.now()}
    state.todos.append(todo)
    state.next_id += 1
    return f"Added todo #{todo['id']}: {task}"


@app.command()
def done(state, todo_id: int):
    """Mark a todo as done."""
    for todo in state.todos:
        if todo["id"] == todo_id:
            if todo["done"]:
                return f"Todo #{todo_id} is already done"
            todo["done"] = True
            todo["completed"] = datetime.now()
            return f"Completed todo #{todo_id}: {todo['task']}"
    return f"Todo #{todo_id} not found"


@app.command()
def undone(state, todo_id: int):
    """Mark a todo as not done."""
    for todo in state.todos:
        if todo["id"] == todo_id:
            if not todo["done"]:
                return f"Todo #{todo_id} is not done"
            todo["done"] = False
            todo.pop("completed", None)
            return f"Reopened todo #{todo_id}: {todo['task']}"
    return f"Todo #{todo_id} not found"


@app.command()
def remove(state, todo_id: int):
    """Remove a todo."""
    for i, todo in enumerate(state.todos):
        if todo["id"] == todo_id:
            removed = state.todos.pop(i)
            return f"Removed todo #{todo_id}: {removed['task']}"
    return f"Todo #{todo_id} not found"


@app.command(display="table", headers=["Metric", "Value"])
def stats(state):
    """Show todo statistics."""
    total = len(state.todos)
    if total == 0:
        return []

    done = sum(1 for t in state.todos if t["done"])
    pending = total - done

    # Priority breakdown
    high = sum(1 for t in state.todos if t.get("priority") == "high" and not t["done"])
    medium = sum(1 for t in state.todos if t.get("priority") == "medium" and not t["done"])
    low = sum(1 for t in state.todos if t.get("priority") == "low" and not t["done"])

    # Calculate completion rate
    completion = f"{done / total * 100:.1f}%" if total > 0 else "N/A"

    # Running time
    running_time = datetime.now() - state.created_at
    days = running_time.days
    hours = running_time.seconds // 3600

    # Return as list of [metric, value] pairs for table display
    return [
        ["Total Todos", str(total)],
        ["Completed", str(done)],
        ["Pending", str(pending)],
        ["Completion Rate", completion],
        ["", ""],  # Separator row
        ["High Priority", str(high)],
        ["Medium Priority", str(medium)],
        ["Low Priority", str(low)],
        ["", ""],  # Separator row
        ["Session Time", f"{days}d {hours}h"],
    ]


@app.command(display="list")
def pending(state, priority: str = None):
    """List pending todos.

    Args:
        priority: Filter by priority (optional)
    """
    pending_todos = [t for t in state.todos if not t["done"]]

    if priority:
        pending_todos = [t for t in pending_todos if t.get("priority") == priority]

    if not pending_todos:
        return []

    return [f"#{t['id']} [{t.get('priority', 'medium').upper()[0]}] {t['task']}" for t in pending_todos]


@app.command(display="tree")
def by_priority(state):
    """Show todos organized by priority."""
    high = [t for t in state.todos if t.get("priority") == "high"]
    medium = [t for t in state.todos if t.get("priority") == "medium"]
    low = [t for t in state.todos if t.get("priority") == "low"]

    def format_todo(t):
        status = "[X]" if t["done"] else "[ ]"
        return f"{status} #{t['id']} - {t['task']}"

    return {
        "High Priority": [format_todo(t) for t in high] if high else ["None"],
        "Medium Priority": [format_todo(t) for t in medium] if medium else ["None"],
        "Low Priority": [format_todo(t) for t in low] if low else ["None"],
    }


@app.command(display="report")
def report(state):
    """Generate a comprehensive todo report."""
    return [
        ("Statistics", stats(state), {"display": "table", "headers": ["Metric", "Value"]}),
        ("All Todos", todos(state), {"display": "table", "headers": ["ID", "Task", "Priority", "Done", "Created"]}),
        ("By Priority", by_priority(state), {"display": "tree"}),
    ]


if __name__ == "__main__":
    app.run(title="Flask-style Todo App")
