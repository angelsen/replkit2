#!/usr/bin/env python3
"""
Todo list example showcasing ReplKit2 and TextKit features.

Run interactively:
    uv run python -i examples/todo.py

Then use:
    >>> list()          # Show todos in a table
    >>> add("Task")     # Add a new todo
    >>> done(0)         # Mark todo as done
    >>> stats()         # Show statistics
    >>> report()        # Full report with multiple displays
"""

from datetime import datetime
from replkit2 import create_repl_app, state, command


@state
class TodoApp:
    """A feature-rich todo list manager."""

    def __init__(self):
        self.todos = []
        self.completed_count = 0

    @command(display="table", headers=["id", "task", "priority", "created", "done"])
    def list(self):
        """Show all todos in a table."""
        return [
            {
                "id": i,
                "task": t["task"][:30],  # Truncate long tasks
                "priority": t["priority"],
                "created": t["created"].strftime("%Y-%m-%d"),
                "done": "[x]" if t["done"] else "[ ]",
            }
            for i, t in enumerate(self.todos)
        ]

    @command
    def add(self, task: str, priority: str = "normal"):
        """Add a new todo with optional priority (low/normal/high)."""
        if priority not in ["low", "normal", "high"]:
            return f"Invalid priority: {priority}. Use low/normal/high"

        self.todos.append(
            {
                "task": task,
                "priority": priority,
                "done": False,
                "created": datetime.now(),
            }
        )
        return f"Added: {task} (priority: {priority})"

    @command
    def done(self, task_id: int):
        """Mark a todo as done."""
        if 0 <= task_id < len(self.todos):
            self.todos[task_id]["done"] = True
            self.completed_count += 1
            return f"Completed: {self.todos[task_id]['task']}"
        return f"Invalid ID: {task_id}"

    @command(display="list", style="check")
    def pending(self):
        """Show only pending todos as a checklist."""
        return [f"{i}: {t['task']}" for i, t in enumerate(self.todos) if not t["done"]]

    @command(display="bar_chart")
    def stats(self):
        """Show todo statistics as a bar chart."""
        total = len(self.todos)
        done = sum(1 for t in self.todos if t["done"])
        pending = total - done

        # Count by priority
        priority_counts = {"low": 0, "normal": 0, "high": 0}
        for t in self.todos:
            if not t["done"]:
                priority_counts[t["priority"]] += 1

        return {
            "Total": total,
            "Done": done,
            "Pending": pending,
            "High Priority": priority_counts["high"],
            "Normal Priority": priority_counts["normal"],
            "Low Priority": priority_counts["low"],
        }

    @command(display="tree")
    def organize(self):
        """Organize todos by priority in a tree view."""
        organized = {"high": [], "normal": [], "low": []}

        for i, t in enumerate(self.todos):
            if not t["done"]:
                organized[t["priority"]].append(f"{i}: {t['task'][:40]}")

        # Only include non-empty priorities
        return {k: v for k, v in organized.items() if v}

    @command(display="progress")
    def completion(self):
        """Show overall completion progress."""
        total = len(self.todos)
        done = sum(1 for t in self.todos if t["done"])

        return {"value": done, "total": total, "label": "Completion"}

    @command
    def report(self):
        """Generate a full report (demonstrates compose)."""
        from replkit2.textkit import compose, hr, box, list_display

        # Get data
        total = len(self.todos)
        done = sum(1 for t in self.todos if t["done"])

        # Build report sections
        summary = box(
            f"Total: {total}\nCompleted: {done}\nPending: {total - done}",
            title="Todo Summary",
        )

        # Get other displays
        pending_list = self.pending()
        pending_display = list_display(pending_list, style="check") if pending_list else "  No pending tasks!"

        # Manual compose since we can't use display hints here
        return compose(
            summary,
            hr(),
            "Pending Tasks:",
            pending_display,
            hr(),
            f"Overall Progress: {done}/{total}",
        )


# Create app and inject commands
app = create_repl_app("todo", TodoApp)

if __name__ == "__main__":
    print("Todo List Manager - ReplKit2 + TextKit Demo")
    print("=" * 50)
    print("Commands:")
    print("  list()                - Show all todos")
    print("  add(task, priority)   - Add todo (priority: low/normal/high)")
    print("  done(id)              - Mark as complete")
    print("  pending()             - Show incomplete todos")
    print("  stats()               - View statistics")
    print("  organize()            - Tree view by priority")
    print("  completion()          - Progress bar")
    print("  report()              - Full report")
    print()
    print("Try: add('Write documentation', 'high')")
    print()
