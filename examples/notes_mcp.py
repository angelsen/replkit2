#!/usr/bin/env python
"""Demo of ReplKit2 with typed FastMCP integration."""

import sys
from dataclasses import dataclass, field
from replkit2 import App


@dataclass
class NotesState:
    notes: list[dict] = field(default_factory=list)
    next_id: int = 1


app = App("notes", NotesState, uri_scheme="noteapp", fastmcp={"tags": {"productivity", "notes"}})


@app.command(display="table", fastmcp={"type": "tool", "tags": {"write", "create"}})
def list_notes(state, tag: str = None):
    """List all notes, optionally filtered by tag."""
    notes = state.notes
    if tag:
        notes = [n for n in notes if tag in n.get("tags", [])]
    return notes


@app.command(fastmcp={"type": "tool"})
def add_note(state, text: str, tags: str = ""):
    """Add a new note with optional comma-separated tags."""
    note = {"id": state.next_id, "text": text, "tags": [t.strip() for t in tags.split(",") if t.strip()]}
    state.notes.append(note)
    state.next_id += 1
    return f"Added note #{note['id']}"


@app.command(
    fastmcp={
        "type": "resource",
        "mime_type": "application/json",
        "description": "Get a summary of all notes in JSON format",
    }
)
def note_summary(state):
    """Get a summary of all notes."""
    return {
        "total_notes": len(state.notes),
        "unique_tags": sorted(set(tag for note in state.notes for tag in note.get("tags", []))),
        "next_id": state.next_id,
    }


@app.command(
    fastmcp={
        "type": "resource",
        "uri": "noteapp://note/{id}",
        "mime_type": "application/json",
        "stub": {
            "response": {
                "example": "noteapp://note/123",
                "description": "Replace :id with a note ID",
                "usage": "Use list_notes to find available note IDs",
            }
        },
    }
)
def get_note(state, id: int):
    """Get a specific note by ID."""
    for note in state.notes:
        if note["id"] == id:
            return note
    return {"error": f"Note {id} not found"}


@app.command(display="box", fastmcp={"type": "prompt", "tags": {"creative", "brainstorm"}})
def brainstorm_prompt(state, topic: str = None):
    """Generate a brainstorming prompt based on existing notes."""
    if not topic:
        tags = set(tag for note in state.notes for tag in note.get("tags", []))
        topic = "your notes" if not tags else f"topics: {', '.join(sorted(tags))}"

    recent_notes = state.notes[-5:] if state.notes else []
    context = "\n".join(f"- {n['text']}" for n in recent_notes)

    prompt = f"Based on {topic}"
    if context:
        prompt += f" and these recent notes:\n{context}\n"
    prompt += "\nWhat are 3 creative ideas to explore next?"

    return prompt


@app.command(fastmcp={"enabled": False})
def clear_notes(state):
    """Clear all notes (not exposed to MCP)."""
    state.notes.clear()
    state.next_id = 1
    return "All notes cleared"


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        print("Starting MCP server...")
        try:
            app.mcp.run()
        except Exception as e:
            print(f"MCP Error: {e}")
            print("\nTry running in REPL mode without --mcp flag")
    else:
        app.run(title="Notes App with FastMCP")
