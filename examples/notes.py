#!/usr/bin/env python
"""Notes app with MCP integration.

Demonstrates: MCP tools/resources/prompts, persistence, markdown display,
message format, ExecutionContext.
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from contextlib import contextmanager
from replkit2 import App
from replkit2.types import ExecutionContext


@dataclass
class NotesState:
    """Pure JSON-based state - reads/writes on each operation."""

    _file_path: Path = field(default_factory=lambda: Path.cwd() / ".notes.json")

    def __post_init__(self):
        """Validate file path stays within intended directory."""
        try:
            resolved_path = self._file_path.resolve()
            cwd = Path.cwd().resolve()
            # Ensure path is within current working directory
            resolved_path.relative_to(cwd)
        except ValueError:
            raise ValueError(
                f"Invalid file path: {self._file_path} is outside current directory. "
                f"For security, notes file must be within {cwd}"
            )

    def read(self) -> dict:
        """Read current state from JSON file."""
        if self._file_path.exists():
            try:
                with open(self._file_path) as f:
                    data = json.load(f)
                    return {"notes": data.get("notes", []), "next_id": data.get("next_id", 1)}
            except (json.JSONDecodeError, OSError):
                pass
        return {"notes": [], "next_id": 1}

    def save(self, notes: List[dict], next_id: int):
        """Save state to JSON file."""
        try:
            with open(self._file_path, "w") as f:
                json.dump({"notes": notes, "next_id": next_id}, f, indent=2, default=str)
        except Exception as e:
            raise Exception(f"Failed to save: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for transactional operations."""
        # Read current state
        data = self.read()
        notes = data["notes"][:]  # Copy for rollback
        next_id = data["next_id"]

        # Create a temporary object with current data
        temp = type("obj", (object,), {"notes": data["notes"], "next_id": data["next_id"]})()

        try:
            yield temp
            # Save on success
            self.save(temp.notes, temp.next_id)
        except Exception:
            # Rollback by saving original
            self.save(notes, next_id)
            raise


# Create app with state class
app = App("notes", NotesState, mcp_config={"uri_scheme": "notes"})

# Create state handler
app.state = NotesState()


@app.command(
    display="table",
    headers=["ID", "Title", "Tags", "Created"],
    fastmcp={
        "type": "tool",
        "aliases": ["ls"],  # Unix-style alias for listing
    },
)
def list(state, tag: str = None):
    """List all notes, optionally filtered by tag."""
    data = state.read()
    notes = data["notes"]

    if not notes:
        return []

    if tag:
        notes = [n for n in notes if tag in n.get("tags", [])]

    return [
        {"ID": str(n["id"]), "Title": n["title"], "Tags": ", ".join(n.get("tags", [])), "Created": n["created"][:10]}
        for n in notes
    ]


@app.command(
    display="box",
    fastmcp={
        "type": "tool",
        "aliases": [
            {"name": "create", "description": "Create a new note"},
            {
                "name": "new",
                "description": "Add a new note entry",
                "param_mapping": {"title": "heading"},  # More semantic: heading instead of title
            },
        ],
    },
)
def add(state, title: str, tags: List[str] = None):
    """Add a new note with explicit save."""
    # Read current state
    data = state.read()
    notes = data["notes"]
    next_id = data["next_id"]

    note = {"id": next_id, "title": title, "tags": tags or [], "created": datetime.now().isoformat()}
    notes.append(note)

    # Save updated state
    state.save(notes, next_id + 1)

    return f"Added note #{note['id']}: {title}"


@app.command(display="box", fastmcp={"type": "tool"})
def bulk_add(state, titles: List[str]):
    """Add multiple notes in a transaction."""
    if not titles:
        return "No titles provided"

    added = []
    with state.transaction() as temp:  # Auto-saves on success, rolls back on error
        for title in titles:
            if len(title) > 100:
                raise ValueError(f"Title too long: {title[:50]}...")

            note = {"id": temp.next_id, "title": title, "tags": ["bulk"], "created": datetime.now().isoformat()}
            temp.notes.append(note)
            temp.next_id += 1
            added.append(note["id"])

    return f"Added {len(added)} notes: {', '.join(f'#{id}' for id in added)}"


@app.command(fastmcp={"type": "resource", "mime_type": "application/json"})
def get(state, id: int):
    """Get a specific note by ID."""
    data = state.read()
    for note in data["notes"]:
        if note["id"] == id:
            return note
    return {"error": f"Note {id} not found"}


@app.command(fastmcp={"type": "resource", "mime_type": "application/json"})
def search(state, query: str, tags: List[str] = None):
    """Search notes by title.

    URI examples:
    - notes://search/meeting
    - notes://search/project/work,urgent
    """
    data = state.read()
    results = []
    for note in data["notes"]:
        if query.lower() in note["title"].lower():
            if not tags or any(t in note.get("tags", []) for t in tags):
                results.append(note)

    return {"query": query, "tags": tags, "results": results, "count": len(results)}


@app.command(
    display="table",
    headers=["ID", "Title", "Tags", "Created"],
    fastmcp={"type": "tool"}
)
def recent(state, limit: int = None, _ctx: ExecutionContext = None):
    """Show recent notes with context-aware defaults.

    Args:
        limit: Max notes to show (default: 5 for REPL, 20 for MCP/CLI)
        _ctx: Execution context (auto-injected by framework)

    Example of context-aware behavior:
    - REPL mode: Shows 5 recent notes (compact for terminal)
    - MCP mode: Shows 20 recent notes (full data for LLM)
    - User can always override with explicit limit parameter
    """
    # Smart defaults based on execution mode
    if limit is None:
        # REPL: compact output for human viewing
        # MCP: more complete data for LLM analysis
        limit = 5 if _ctx and _ctx.is_repl() else 20

    data = state.read()
    notes = data["notes"]

    if not notes:
        return []

    # Sort by created date (newest first) and apply limit
    sorted_notes = sorted(notes, key=lambda n: n.get("created", ""), reverse=True)[:limit]

    return [
        {
            "ID": str(n["id"]),
            "Title": n["title"],
            "Tags": ", ".join(n.get("tags", [])),
            "Created": n["created"][:10]
        }
        for n in sorted_notes
    ]


@app.command(display="box", fastmcp={"type": "tool"})
def delete(state, id: int):
    """Delete a note by ID with explicit save."""
    data = state.read()
    notes = data["notes"]
    initial_count = len(notes)

    notes = [n for n in notes if n["id"] != id]

    if len(notes) < initial_count:
        state.save(notes, data["next_id"])
        return f"Deleted note #{id}"
    return f"Note #{id} not found"


@app.command(display="box", fastmcp={"type": "tool"})
def update(state, id: int, title: str = None, tags: List[str] = None):
    """Update a note using transaction for safety."""
    with state.transaction() as temp:  # Ensures consistency
        for note in temp.notes:
            if note["id"] == id:
                if title:
                    note["title"] = title
                if tags is not None:
                    note["tags"] = tags
                note["updated"] = datetime.now().isoformat()
                return f"Updated note #{id}"
        raise ValueError(f"Note #{id} not found")


@app.command(display="tree", fastmcp={"type": "tool"})
def tags(state):
    """Show all tags and their note counts."""
    data = state.read()
    notes = data["notes"]

    tag_counts = {}
    for note in notes:
        for tag in note.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if not tag_counts:
        return {}

    return {
        "Tags": {
            f"{tag} ({count} notes)": [n["title"] for n in notes if tag in n.get("tags", [])][:3]
            for tag, count in sorted(tag_counts.items())
        }
    }


@app.command(fastmcp={"type": "prompt"})
def summarize(state, topic: str = "all"):
    """Generate a summary prompt for notes."""
    data = state.read()
    all_notes = data["notes"]

    notes = (
        all_notes
        if topic == "all"
        else [n for n in all_notes if topic in n.get("tags", []) or topic.lower() in n["title"].lower()]
    )

    if not notes:
        return f"No notes found for topic: {topic}"

    prompt = f"Summarize these {len(notes)} notes"
    if topic != "all":
        prompt += f" about {topic}"
    prompt += ":\n\n"

    for note in notes[:10]:
        prompt += f"- {note['title']} (tags: {', '.join(note.get('tags', []))})\n"

    return prompt


@app.command(fastmcp={"enabled": False})
def init(state):
    """Initialize with sample data (REPL only)."""
    data = state.read()
    if data["notes"]:
        return "Notes already exist. Use 'clear' first."

    samples = [
        ("Team meeting notes", ["work", "meeting"]),
        ("Project roadmap", ["work", "planning"]),
        ("Shopping list", ["personal"]),
        ("Bug: validation error", ["bug", "urgent"]),
        ("Learn FastMCP", ["learning"]),
    ]

    # Use transaction for atomic initialization
    with state.transaction() as temp:
        for title, tags in samples:
            note = {"id": temp.next_id, "title": title, "tags": tags, "created": datetime.now().isoformat()}
            temp.notes.append(note)
            temp.next_id += 1

    return f"Initialized with {len(samples)} sample notes"


@app.command(fastmcp={"enabled": False})
def clear(state):
    """Clear all notes (REPL only)."""
    data = state.read()
    count = len(data["notes"])
    state.save([], 1)  # Save empty state
    return f"Cleared {count} notes"


@app.command(display="box", fastmcp={"type": "tool"})
def stats(state):
    """Show statistics without modifying state."""
    data = state.read()
    notes = data["notes"]

    total = len(notes)
    tag_count = len(set(tag for n in notes for tag in n.get("tags", [])))
    recent = sum(1 for n in notes if n.get("created", "")[:10] == datetime.now().isoformat()[:10])

    return f"Total: {total} notes\nTags: {tag_count} unique\nToday: {recent} notes"


@app.command(display="markdown", fastmcp={"type": "prompt"})
def review(state, topic: str):
    """Review notes - demonstrates MCP message format with elements content."""
    data = state.read()
    matching = [n for n in data["notes"] if topic.lower() in n["title"].lower()][:3]

    return {
        "messages": [
            {"role": "system", "content": {"type": "elements", "elements": [
                {"type": "text", "content": "You are reviewing notes."}
            ]}},
            {"role": "user", "content": {"type": "elements", "elements": [
                {"type": "heading", "content": f"Notes about '{topic}'"},
                {"type": "table", "headers": ["ID", "Title", "Tags"],
                 "rows": [{"ID": str(n["id"]), "Title": n["title"],
                          "Tags": ", ".join(n.get("tags", []))} for n in matching]},
                {"type": "alert", "content": f"Found {len(matching)} matching notes", "level": "info"}
            ]}}
        ]
    }


@app.command(display="markdown")
def report(state, tag: str = None):
    """Generate note report - demonstrates frontmatter and markdown builder."""
    from replkit2.textkit import markdown

    data = state.read()
    notes = [n for n in data["notes"] if not tag or tag in n.get("tags", [])]

    return (markdown()
        .frontmatter(title="Notes Report", tag=tag or "all", generated=True)
        .heading("Summary")
        .text(f"Found {len(notes)} notes" + (f" with tag '{tag}'" if tag else ""))
        .table(headers=["ID", "Title", "Created"],
               rows=[{"ID": str(n["id"]), "Title": n["title"],
                      "Created": n["created"][:10]} for n in notes[:5]])
        .build())


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        app.mcp.run()
    else:
        app.run(title="Notes App with Explicit Persistence")
