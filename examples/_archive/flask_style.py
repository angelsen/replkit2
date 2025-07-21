"""
Flask-style ReplKit2 example showing the recommended API patterns.

This example demonstrates:
- Using App() directly instead of create_repl_app()
- Flask-style command decorators
- Using app.run() instead of app.start_repl()
"""

from dataclasses import dataclass, field
from replkit2 import App


@dataclass
class TodoState:
    """State container for our todo application."""

    todos: list[dict] = field(default_factory=list)
    next_id: int = 1


# Create the app with state
app = App("todo-flask", TodoState)


@app.command(display="table", headers=["ID", "Task", "Done"])
def list_todos(state):
    """List all todos in a table format."""
    if not state.todos:
        return []
    return [{"ID": t["id"], "Task": t["task"], "Done": "✓" if t["done"] else "✗"} for t in state.todos]


@app.command()
def add(state, task: str):
    """Add a new todo task."""
    todo = {"id": state.next_id, "task": task, "done": False}
    state.todos.append(todo)
    state.next_id += 1
    return f"Added todo #{todo['id']}: {task}"


@app.command()
def done(state, todo_id: int):
    """Mark a todo as done."""
    for todo in state.todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            return f"Marked todo #{todo_id} as done"
    return f"Todo #{todo_id} not found"


@app.command()
def remove(state, todo_id: int):
    """Remove a todo."""
    for i, todo in enumerate(state.todos):
        if todo["id"] == todo_id:
            state.todos.pop(i)
            return f"Removed todo #{todo_id}"
    return f"Todo #{todo_id} not found"


@app.command(display="box", title="Todo Stats")
def stats(state):
    """Show todo statistics."""
    total = len(state.todos)
    done = sum(1 for t in state.todos if t["done"])
    pending = total - done

    return {
        "Total": total,
        "Done": done,
        "Pending": pending,
        "Completion": f"{done / total * 100:.1f}%" if total > 0 else "N/A",
    }


if __name__ == "__main__":
    print("Flask-style Todo App")
    print("Commands: list_todos(), add(task), done(id), remove(id), stats()")
    print("-" * 50)

    # Run the REPL
    app.run()
