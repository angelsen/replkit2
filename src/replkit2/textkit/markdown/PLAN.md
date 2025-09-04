# ReplKit2 Markdown Module Refactor Plan

## Overview

Clean break refactor to restructure the markdown module into a proper package with separation of concerns, adding display-level truncation and transforms. This is a **breaking change** with no migration path.

## Goals

1. **Modular structure**: Split monolithic markdown.py into focused modules
2. **Display control**: Add truncation and transforms at render time
3. **Native elements**: Include Table and Alert as first-class elements
4. **MCP consistency**: Ensure both tools and resources respect mime_type

## File Structure

```
src/replkit2/textkit/markdown/
├── __init__.py       # Public API exports
├── base.py           # MarkdownElement base class
├── elements.py       # Core elements (text, heading, code_block, etc.)
├── table.py          # Table element with truncation/transforms
├── alert.py          # Alert element with severity levels
├── transforms.py     # Common data transformations
├── builder.py        # markdown() builder utility
└── PLAN.md          # This file
```

## Breaking Changes

### 1. Import Paths
```python
# OLD - Will break
from replkit2.textkit.markdown import MarkdownElement, markdown

# NEW - Required
from replkit2.textkit.markdown import MarkdownElement  # from __init__
from replkit2.textkit.markdown.builder import markdown  # if needed directly
```

### 2. Element Registration
- Self-registration via `__init_subclass__` removed
- Explicit element type registry in `__init__.py`

### 3. New Required Fields
- Table element gains `truncate` and `transforms` parameters
- Alert element added (not a breaking change, but new)

## Implementation Tasks

### Phase 1: Core Structure ✅
- [x] Create `base.py` with MarkdownElement base class
- [x] Create `elements.py` with existing elements (text, heading, code_block, etc.)
- [x] Create `__init__.py` with proper exports
- [ ] Remove old `markdown.py` file

### Phase 2: New Elements ✅
- [x] Create `table.py` with Table element
  - [x] Port WebTap's table rendering logic
  - [x] Add truncation support
  - [x] Add transform support
- [x] Create `alert.py` with Alert element
  - [x] Use existing ICONS from `textkit/icons.py`
  - [x] Support severity levels (error, warning, info, success)

### Phase 3: Transforms ✅
- [x] Create `transforms.py` with common transformations
  - [x] `format_size()` - bytes to human readable
  - [x] `format_timestamp()` - ms to readable time
  - [x] `format_number()` - number formatting with commas
  - [x] `format_duration()` - seconds to human readable
  - [x] Added bonus: `format_percentage()`, `format_boolean()`
- [x] Add transform registry and lookup system
- [x] Integrate transforms into Table rendering

### Phase 4: Builder Updates ✅
- [x] Update `builder.py` to work with new structure
- [x] Ensure backward compatibility for builder API
- [x] Add methods for new Table and Alert elements

### Phase 5: Integration ✅
- [x] Update `textkit/formatter.py` to handle new markdown structure
- [x] Markdown module now properly structured
- [ ] Test with existing examples

### Phase 6: ~~Runtime Formatting~~ (Removed - unnecessary complexity)
- ~~Create `src/replkit2/formatting.py` with RuntimeFormat class~~
- ~~Update `app.py` to detect and handle RuntimeFormat~~
- ~~Update MCP integration to handle RuntimeFormat~~
- ~~Update CLI integration to handle RuntimeFormat~~

### Phase 7: MCP Consistency ✅
- [x] Tool MIME type handling already works in `integrations/mcp.py`
- [x] Tools respect `mime_type="text/*"` via `_call_function_with_formatting`
- [ ] Test with WebTap's dual-mode commands

### Phase 8: CommandMeta Extensions ✅
- [x] Add `truncate` field to CommandMeta
- [x] Add `transforms` field to CommandMeta
- [x] Update decorator to accept truncate/transforms parameters

## Testing Strategy

### Unit Tests Required
- [ ] Test each element's render() method
- [ ] Test truncation modes (start, middle, end)
- [ ] Test all transforms with edge cases
- [ ] Test Table with various data shapes
- [ ] Test Alert with all severity levels

### Integration Tests Required
- [ ] Test markdown formatter with new elements
- [ ] Test RuntimeFormat in REPL mode
- [ ] Test RuntimeFormat in MCP mode
- [ ] Test RuntimeFormat in CLI mode
- [ ] Test WebTap commands with new system

## Success Criteria

1. **Clean separation**: Each file has single responsibility
2. **No data loss**: Full data preserved until render time
3. **Consistent behavior**: Tools and resources format identically
4. **Runtime control**: Can override formatting at runtime
5. **Performance**: No regression in rendering speed

## WebTap Benefits

After this refactor, WebTap can:
1. Remove `_markdown.py` entirely
2. Remove `_symbols.py` entirely  
3. Remove formatting functions from `_utils.py`
4. Return full data in all commands
5. Use declarative truncation/transforms

## Example Usage After Refactor

```python
from replkit2.textkit.markdown import Table, Alert

@app.command(
    display="markdown",
    truncate={
        "URL": {"max": 60, "mode": "middle"},
        "ID": {"max": 12}
    },
    transforms={
        "Size": "format_size",
        "Time": "format_timestamp"
    },
    fastmcp=[
        {"type": "resource", "mime_type": "text/markdown"},  # Formatted
        {"type": "tool"}  # Raw JSON data
    ]
)
def network(state):
    # Return FULL data - no truncation at data level
    data = get_network_data()
    
    # Return structured markdown
    return {
        "elements": [
            {"type": "heading", "content": "Network Data", "level": 2},
            Table(headers, rows).to_dict(),
            Alert("Filters applied", level="info").to_dict()
        ]
    }
    
    # REPL: Formats using display="markdown" with truncation/transforms
    # MCP Resource: Formats to markdown text (mime_type="text/markdown")
    # MCP Tool: Returns raw JSON structure (no mime_type)
```

## Notes

- **No backward compatibility** - This is a clean break
- **No deprecation warnings** - Old code will fail immediately
- **No migration tools** - Users must update imports manually
- **Version bump** - This warrants v0.10.0 (not 1.0.0)

## Timeline

Estimated: 2-3 days for full implementation and testing

## Status

**Started**: 2025-09-02  
**Completed**: 2025-09-04  
**Phase**: Complete with extensible truncation system  
**Blockers**: None  
**Next Steps**: Testing and integration with WebTap

## Extensible Truncation System (v0.10.1)

The markdown module now supports command-level truncation/transforms that are automatically applied to supporting elements:

### How It Works

1. **Elements declare capabilities** via class attributes:
   ```python
   class MyElement(MarkdownElement):
       element_type = "my_element"
       supports_truncation = True  # Opt-in to truncation
       supports_transforms = True   # Opt-in to transforms
   ```

2. **Command-level settings are defaults**:
   ```python
   @app.command(
       display="markdown",
       truncate={"col": {"max": 50}},  # Applied to all supporting elements
       transforms={"size": "format_size"}
   )
   ```

3. **Element-level settings override**:
   ```python
   {
       "type": "table",
       "truncate": {"col": {"max": 30}},  # Overrides command-level
       ...
   }
   ```

### Adding Truncation to New Elements

To add truncation support to a new element:

1. Set `supports_truncation = True` in the element class
2. Accept `truncate` parameter in `__init__` and `from_dict`
3. Apply truncation in `render()` method

Example:
```python
class List(MarkdownElement):
    element_type = "list"
    supports_truncation = True  # Opt-in
    
    def __init__(self, items, truncate=None):
        self.items = items
        self.truncate = truncate
    
    def render(self):
        if self.truncate:
            # Apply truncation to items
            items = [self._truncate_value(item, self.truncate) for item in self.items]
        else:
            items = self.items
        # ... render list
```

### Currently Supporting Elements

- **Table**: Full support for truncation and transforms