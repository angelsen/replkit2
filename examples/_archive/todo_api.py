#!/usr/bin/env python3
"""
FastAPI + ReplKit2 example - Same todo app, different serialization.

This demonstrates how the same TodoApp can be used for both:
- REPL with ASCII formatting (TextSerializer)
- API with JSON responses (PassthroughSerializer)

Run the API server:
    uv run --extra api uvicorn examples.todo_api:app --reload

API endpoints:
    GET    /               - Interactive docs
    GET    /todos          - List all todos
    POST   /todos          - Create a new todo
    PATCH  /todos/{id}     - Mark todo as done
    DELETE /todos/{id}     - Remove a todo
    GET    /stats          - Todo statistics
    GET    /report         - Full report (ASCII formatted)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from replkit2 import App, PassthroughSerializer, JSONSerializer
from replkit2.textkit import TextSerializer

# Import the TodoApp from our REPL example
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from todo import TodoApp  # pyright: ignore[reportImplicitRelativeImport]


# Pydantic models for API
class TodoCreate(BaseModel):
    task: str
    priority: str = "normal"


# Create the main app with PassthroughSerializer for API responses
app_instance = App("todo_api", serializer=PassthroughSerializer())
app_instance.register(TodoApp)

# Create different views using the same state
text_view = app_instance.with_serializer(TextSerializer())
json_view = app_instance.with_serializer(JSONSerializer())

# Aliases for backwards compatibility
api_app = app_instance
text_app = text_view

# Create FastAPI app
app = FastAPI(
    title="Todo API",
    description="Same TodoApp, different presentation layer",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Redirect to docs."""
    return {"message": "Visit /docs for interactive API documentation"}


@app.get("/todos")
async def list_todos():
    """List all todos as JSON."""
    return api_app.execute("list")


@app.post("/todos")
async def create_todo(todo: TodoCreate):
    """Create a new todo."""
    result = api_app.execute("add", todo.task, todo.priority)

    # Extract task from the response string
    if isinstance(result, str) and result.startswith("Added:"):
        # Get the newly created todo
        todos = api_app.execute("list")
        return todos[-1] if todos else {"error": "Todo not created"}

    return {"error": result}


@app.patch("/todos/{todo_id}")
async def complete_todo(todo_id: int):
    """Mark a todo as done."""
    result = api_app.execute("done", todo_id)

    if isinstance(result, str):
        if result.startswith("Completed:"):
            # Get the updated todo
            todos = api_app.execute("list")
            for todo in todos:
                if todo["id"] == todo_id:
                    return todo
            return {"error": "Todo not found after update"}
        else:
            raise HTTPException(status_code=404, detail=result)

    return result


@app.delete("/todos/{todo_id}")
async def remove_todo(todo_id: int):
    """Remove a todo."""
    # Get todo before deletion
    todos = api_app.execute("list")
    todo_to_delete = None
    for todo in todos:
        if todo["id"] == todo_id:
            todo_to_delete = todo
            break

    if not todo_to_delete:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")

    result = api_app.execute("remove", todo_id)

    if isinstance(result, str) and result.startswith("Removed:"):
        return todo_to_delete
    else:
        raise HTTPException(status_code=400, detail=result)


@app.get("/stats")
async def get_stats():
    """Get todo statistics as JSON."""
    return api_app.execute("stats")


@app.get("/pending")
async def get_pending():
    """Get pending todos as JSON."""
    return api_app.execute("pending")


@app.get("/report")
async def get_report():
    """Get full report as ASCII text."""
    from fastapi.responses import PlainTextResponse

    # Use the text app for formatted output
    return PlainTextResponse(text_app.execute("report"))


@app.get("/export/table")
async def export_table():
    """Export todos as ASCII table."""
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(text_app.execute("list"))


@app.get("/export/tree")
async def export_tree():
    """Export todos organized by priority as ASCII tree."""
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(text_app.execute("organize"))


@app.get("/export/json")
async def export_json():
    """Export todos as formatted JSON."""
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(json_view.execute("list"), media_type="application/json")


@app.get("/health")
async def health_check():
    """API health check."""
    stats = api_app.execute("stats")
    return {"status": "healthy", "service": "todo-api", "todos": stats}


if __name__ == "__main__":
    print("Todo API - Reusing TodoApp with Different Serializers")
    print("=" * 50)
    print()
    print("This demonstrates the same TodoApp being used for:")
    print("- JSON API responses (PassthroughSerializer)")
    print("- ASCII text responses (TextSerializer)")
    print()
    print("Start the server:")
    print("  uv run --extra api uvicorn examples.todo_api:app --reload")
    print()
    print("Then visit:")
    print("  http://localhost:8000/docs     - Interactive API docs")
    print("  http://localhost:8000/todos    - JSON todo list")
    print("  http://localhost:8000/report   - ASCII formatted report")
    print("  http://localhost:8000/export/table - ASCII table export")
