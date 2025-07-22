#!/usr/bin/env python3
"""
FastAPI + ReplKit2 Flask-style Example

This demonstrates how Flask-style ReplKit2 apps integrate with web frameworks:
- Same TodoState used for both REPL and API
- Different formatters for different outputs
- Clean separation of concerns

Run the API server:
    uv run --extra api uvicorn examples.todo_api:app --reload

API endpoints:
    GET    /               - Interactive API docs
    GET    /todos          - List all todos
    POST   /todos          - Create a new todo
    PATCH  /todos/{id}     - Update a todo
    DELETE /todos/{id}     - Remove a todo
    GET    /stats          - Todo statistics
    GET    /report         - Full report (JSON)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from replkit2 import PassthroughFormatter
from replkit2.textkit import TextFormatter

# Import our state from the todo example
from todo import app as todo_app


# Pydantic models for API
class TodoCreate(BaseModel):
    task: str
    priority: str = "medium"


class TodoUpdate(BaseModel):
    done: Optional[bool] = None
    task: Optional[str] = None
    priority: Optional[str] = None


class TodoResponse(BaseModel):
    id: int
    task: str
    priority: str
    done: bool
    created: datetime
    completed: Optional[datetime] = None


# Create FastAPI app
api = FastAPI(title="Todo API", description="ReplKit2 Flask-style Todo API")

# Use the imported todo_app with different formatters
state = todo_app.state  # Use the state from the imported app
json_app = todo_app.using(PassthroughFormatter())
text_app = todo_app.using(TextFormatter())


@api.get("/")
def root():
    """API root - redirects to docs."""
    return {"message": "Todo API", "docs": "/docs"}


@api.get("/todos", response_model=list[TodoResponse])
def get_todos():
    """List all todos."""
    return state.todos


@api.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    """Create a new todo."""
    json_app.execute("add", todo.task, todo.priority)
    return state.todos[-1]


@api.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    """Get a specific todo."""
    for todo in state.todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@api.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, update: TodoUpdate):
    """Update a todo."""
    for todo in state.todos:
        if todo["id"] == todo_id:
            # Update fields if provided
            if update.task is not None:
                todo["task"] = update.task
            if update.priority is not None:
                todo["priority"] = update.priority
            if update.done is not None:
                if update.done and not todo["done"]:
                    # Marking as done
                    json_app.execute("done", todo_id)
                elif not update.done and todo["done"]:
                    # Marking as undone
                    json_app.execute("undone", todo_id)
            return todo
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@api.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Delete a todo."""
    # Check if exists
    for todo in state.todos:
        if todo["id"] == todo_id:
            result = json_app.execute("remove", todo_id)
            return {"message": result}
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@api.get("/stats")
def get_stats():
    """Get todo statistics."""
    # Use the stats command
    return json_app.execute("stats")


@api.get("/report")
def get_report():
    """Get a full todo report."""
    # Get data from various commands
    return {
        "stats": json_app.execute("stats"),
        "todos": json_app.execute("todos"),
        "by_priority": json_app.execute("by_priority"),
        "pending_high": json_app.execute("pending", "high"),
        "generated_at": datetime.now().isoformat(),
    }


@api.get("/report/text", response_class=str)
def get_text_report():
    """Get a text-formatted report (ASCII art)."""
    # Use text formatter for ASCII output
    report_parts = []

    # Add stats box
    stats_output = text_app.execute("stats")
    report_parts.append("=== STATISTICS ===\n" + stats_output)

    # Add todos table
    todos_output = text_app.execute("todos")
    report_parts.append("\n=== ALL TODOS ===\n" + todos_output)

    # Add priority tree
    priority_output = text_app.execute("by_priority")
    report_parts.append("\n=== BY PRIORITY ===\n" + priority_output)

    return "\n".join(report_parts)


# Add startup event to populate some sample data
@api.on_event("startup")
def startup_event():
    """Add some sample todos on startup."""
    if not state.todos:
        json_app.execute("add", "Build a REST API", "high")
        json_app.execute("add", "Add authentication", "high")
        json_app.execute("add", "Write API documentation", "medium")
        json_app.execute("add", "Add unit tests", "medium")
        json_app.execute("add", "Deploy to production", "low")
        json_app.execute("done", 3)  # Mark documentation as done
