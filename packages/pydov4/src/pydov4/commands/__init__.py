"""PyDoV4 commands v3 - aligned with ReplKit2 best practices.

Key principles:
1. Always return Python data structures (dicts, lists, strings)
2. Default to native TextKit display types (table, box, tree, list)
3. Use custom displays only when they add real value (e.g., code with diagnostics)
4. Consistent error handling (return [] for tables, {} for trees)
5. Let formatters handle all formatting
"""

# Import all command modules to register with app
from . import core
from . import diagnostics
from . import navigation
from . import workspace
from . import actions

__all__ = ["core", "diagnostics", "navigation", "workspace", "actions"]
