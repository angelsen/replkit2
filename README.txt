================================================================================

                               ReplKit2 - README                                

                             Rendered with TextKit                              

================================================================================

+-- H1 ------------------------------------------------------------------------+
| REPLKIT2 EXAMPLES                                                            |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

This directory contains examples demonstrating the Flask-style API introduced in

ReplKit2 v2.0.

+-- H2 ------------------------------------------------------------------------+
| Quick Start                                                                  |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

All examples use the modern Flask-style pattern:

+-- CODE ----------------------------------------------------------------------+
| from replkit2 import App                                                     |
|                                                                              |
| # Create app with state                                                      |
| app = App("myapp", MyState)                                                  |
|                                                                              |
| # Define commands with decorators                                            |
| @app.command()                                                               |
| def hello(state, name: str = "World"):                                       |
|     return f"Hello, {name}!"                                                 |
|                                                                              |
| # Run the REPL with a banner                                                 |
| app.run(title="My Application")                                              |
+------------------------------------------------------------------------------+

+-- H2 ------------------------------------------------------------------------+
| Examples                                                                     |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

+-- H3 ------------------------------------------------------------------------+
| todo.py - Todo List Manager                                                  |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

A full-featured todo application demonstrating:

* State management with dataclasses
* Multiple display types (table, box, tree, list)
* Command parameters and validation
* Custom display handler for multi-section reports
* Auto-generated help() command

+-- CODE ----------------------------------------------------------------------+
| uv run python examples/todo.py                                               |
+------------------------------------------------------------------------------+

+-- H3 ------------------------------------------------------------------------+
| monitor.py - System Monitor                                                  |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

Real-time system monitoring showing:

* CPU, memory, disk, and network stats
* Progress bars and charts
* Table formatting for processes
* Integration with psutil

+-- CODE ----------------------------------------------------------------------+
| uv run python examples/monitor.py                                            |
+------------------------------------------------------------------------------+

+-- H3 ------------------------------------------------------------------------+
| todo_api.py - FastAPI Integration                                            |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

The same todo app exposed as a REST API:

* Shared state between REPL and API
* Different serializers for different outputs
* Pydantic models for validation
* Auto-generated API documentation

+-- CODE ----------------------------------------------------------------------+
| uv run --extra api uvicorn examples.todo_api:app --reload                    |
+------------------------------------------------------------------------------+

+-- H3 ------------------------------------------------------------------------+
| readme.py - Markdown Renderer                                                |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

A standalone utility showing TextKit's display capabilities:

* No REPL functionality, just rendering
* Converts markdown to ASCII art
* Demonstrates box, table, and text formatting

+-- CODE ----------------------------------------------------------------------+
| uv run python examples/readme.py                                             |
+------------------------------------------------------------------------------+

+-- H2 ------------------------------------------------------------------------+
| Key Concepts                                                                 |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

+-- H3 ------------------------------------------------------------------------+
| Flask-style Commands                                                         |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

Commands are defined as functions decorated with [@app.command()]:

+-- CODE ----------------------------------------------------------------------+
| @app.command(display="table", headers=["ID", "Name", "Status"])              |
| def list_items(state):                                                       |
|     return [{"ID": 1, "Name": "Item", "Status": "Active"}]                   |
+------------------------------------------------------------------------------+

+-- H3 ------------------------------------------------------------------------+
| State Management                                                             |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

State is a separate dataclass passed to commands:

+-- CODE ----------------------------------------------------------------------+
| @dataclass                                                                   |
| class MyState:                                                               |
|     items: list[dict] = field(default_factory=list)                          |
|                                                                              |
| app = App("myapp", MyState)                                                  |
+------------------------------------------------------------------------------+

+-- H3 ------------------------------------------------------------------------+
| Display Hints                                                                |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

Control output formatting with display hints:

* `display="table"` - Tabular data with headers
* `display="box"` - Bordered text with optional title
* `display="list"` - Bullet lists
* `display="tree"` - Hierarchical data
* `display="bar_chart"` - Horizontal bar charts
* `display="progress"` - Progress bars

+-- H3 ------------------------------------------------------------------------+
| Custom Display Handlers                                                      |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

Create custom display types for complex layouts:

+-- CODE ----------------------------------------------------------------------+
| # Register a custom display handler                                          |
| @app.serializer.register("report")                                           |
| def handle_report(data, meta):                                               |
|     from replkit2.textkit import compose, box                                |
|     sections = []                                                            |
|     for title, section_data, opts in data:                                   |
| section_meta = CommandMeta(display=opts.get("display"), display_opts=opts)   |
|         serialized = app.serializer.serialize(section_data, section_meta)    |
|         sections.append(box(serialized, title=title))                        |
|     return compose(*sections, spacing=1)                                     |
|                                                                              |
| # Use the custom display                                                     |
| @app.command(display="report")                                               |
| def report(state):                                                           |
|     return [                                                                 |
|         ("Summary", get_summary(state), {"display": "box"}),                 |
|         ("Details", get_details(state), {"display": "table"}),               |
|         ("Breakdown", get_breakdown(state), {"display": "tree"})             |
|     ]                                                                        |
+------------------------------------------------------------------------------+

+-- H2 ------------------------------------------------------------------------+
| Running Examples                                                             |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

1. Install ReplKit2:

+-- CODE ----------------------------------------------------------------------+
| uv add replkit2                                                              |
+------------------------------------------------------------------------------+

1. For the API example, install extras:

+-- CODE ----------------------------------------------------------------------+
| uv add replkit2[api]                                                         |
+------------------------------------------------------------------------------+

1. Run any example:

+-- CODE ----------------------------------------------------------------------+
| uv run python examples/todo.py                                               |
+------------------------------------------------------------------------------+

+-- H2 ------------------------------------------------------------------------+
| Old Examples                                                                 |
+------------------------------------------------------------------------------+
--------------------------------------------------------------------------------

The previous decorator-based examples are archived in [_archive/] for reference.

The Flask-style pattern is now the recommended approach for all new ReplKit2

applications.

================================================================================

                       Generated from examples/README.md                        

================================================================================
