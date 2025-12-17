#!/usr/bin/env python3
"""
FastAPI + ReplKit2 Integration Example

Demonstrates integrating ReplKit2 state with FastAPI:
- Shared TodoState between REPL and API
- Direct state access for API responses
- Commands for business logic/side effects
- Swagger UI at /docs

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
    GET    /report/text    - Full report (ASCII)
    GET    /context-demo   - ExecutionContext usage example
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import our state from the todo example
from todo import app as todo_app
from replkit2.types import ExecutionContext


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
api = FastAPI(title="Todo API", description="ReplKit2 Todo API")

# Access shared state directly
state = todo_app.state


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
    # Use command for business logic
    todo_app.execute("add", todo.task, todo.priority)
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
            if update.task is not None:
                todo["task"] = update.task
            if update.priority is not None:
                todo["priority"] = update.priority
            if update.done is not None:
                if update.done and not todo["done"]:
                    # Marking as done
                    todo_app.execute("done", todo_id)
                elif not update.done and todo["done"]:
                    # Marking as undone
                    todo_app.execute("undone", todo_id)
            return todo
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@api.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Delete a todo."""
    # Check if exists
    for todo in state.todos:
        if todo["id"] == todo_id:
            result = todo_app.execute("remove", todo_id)
            return {"message": result}
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@api.get("/stats")
def get_stats():
    """Get todo statistics."""
    # Use the stats command
    return todo_app.execute("stats")


@api.get("/report")
def get_report():
    """Get a full todo report."""
    # Get data from various commands
    return {
        "stats": todo_app.execute("stats"),
        "todos": todo_app.execute("todos"),
        "by_priority": todo_app.execute("by_priority"),
        "pending_high": todo_app.execute("pending", "high"),
        "generated_at": datetime.now().isoformat(),
    }


@api.get("/report/text", response_class=PlainTextResponse)
def get_text_report():
    """Get a text-formatted report (ASCII art)."""
    # Get raw data and format using app's formatter
    report_parts = []

    # Stats section
    stats_data = todo_app.execute("stats")
    _, stats_meta = todo_app._commands["stats"]
    stats_output = todo_app.formatter.format(stats_data, stats_meta)
    report_parts.append("=== STATISTICS ===\n" + stats_output)

    # Todos table
    todos_data = todo_app.execute("todos")
    _, todos_meta = todo_app._commands["todos"]
    todos_output = todo_app.formatter.format(todos_data, todos_meta)
    report_parts.append("\n=== ALL TODOS ===\n" + todos_output)

    # Priority tree
    priority_data = todo_app.execute("by_priority")
    _, priority_meta = todo_app._commands["by_priority"]
    priority_output = todo_app.formatter.format(priority_data, priority_meta)
    report_parts.append("\n=== BY PRIORITY ===\n" + priority_output)

    return "\n".join(report_parts)


@api.get("/context-demo")
def context_demo():
    """Demonstrate ExecutionContext usage in programmatic mode.

    Shows how to pass explicit context when calling ReplKit2 commands
    from external code (like FastAPI endpoints).

    This is useful when you want commands to behave differently when
    called from API vs REPL vs MCP.
    """
    # Create programmatic context (default when calling from code)
    prog_ctx = ExecutionContext.for_programmatic()

    # Example: Call command with explicit context
    # (In this case, todos command doesn't use context, but this shows the pattern)
    todos_data = todo_app.execute("todos", _ctx=prog_ctx)

    # You could also create other contexts to simulate different modes
    repl_ctx = ExecutionContext.for_repl()
    mcp_ctx = ExecutionContext.for_mcp(component_type="tool")

    return {
        "message": "ExecutionContext demo for programmatic usage",
        "context_info": {
            "mode": prog_ctx.mode.value,
            "transport": prog_ctx.transport.value,
            "is_programmatic": prog_ctx.is_programmatic()
        },
        "todos_count": len(todos_data),
        "note": (
            "Context-aware commands can check _ctx.is_programmatic(), "
            "_ctx.is_repl(), _ctx.is_mcp() to adapt their behavior. "
            "See examples/context_demo.py for commands that use context."
        )
    }


# Add startup event to populate some sample data
@api.on_event("startup")
def startup_event():
    """Add some sample todos on startup."""
    if not state.todos:
        todo_app.execute("add", "Build a REST API", "high")
        todo_app.execute("add", "Add authentication", "high")
        todo_app.execute("add", "Write API documentation", "medium")
        todo_app.execute("add", "Add unit tests", "medium")
        todo_app.execute("add", "Deploy to production", "low")
        todo_app.execute("done", 3)  # Mark documentation as done
