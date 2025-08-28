# Changelog

All notable changes to ReplKit2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.8.1] - 2025-08-28

### Added

### Changed

### Fixed
- Case-insensitive header matching in table formatter
  - Headers like "ID", "Method", "Status" now match data keys like "id", "method", "status"
  - Maintains backward compatibility while making the framework more forgiving

### Removed

## [0.8.0] - 2025-08-27

### Added
- Generic typing support for `App[S]` providing better IDE hints for state
- `state_args` parameter in `App.__init__()` for passing initialization arguments to state class
- Auto-expose `state` in REPL namespace for easier debugging
- Dual-mode MCP registration support - commands can be both resources and tools
  - `fastmcp` parameter now accepts list of configs: `fastmcp=[{...}, {...}]`
  - `args` field in MCP configs for explicit parameter control
  - Empty `args: []` forces resource with no parameters

### Changed
- **BREAKING**: State attribute is now public (`app.state`) instead of private (`app._state`)
  - Migration: Replace `app._state` with `app.state` in your code
  - This provides cleaner API access without accessing private attributes
- Enhanced `execute()` method with smart state injection based on function signature
  - Commands can now opt-in to receive state parameter instead of always requiring it
- Improved `using()` method to preserve state_class reference correctly
- Simplified MCP integration internals
  - Unified wrapper creation with single `_create_wrapper()` method
  - Optimized parameter filtering in `_call_function_with_formatting()`

### Fixed

### Removed

## [0.7.6] - 2025-08-13

### Added

### Changed
- Made changelog relkit-compatible by adding [Unreleased] section
- Removed date stamps from early version entries (0.1.0-0.3.0) for consistency

### Fixed

### Removed

## [0.7.5] - 2025-08-11

### Added
- Type definition for MCP tool aliases (`FastMCPToolAlias`)
  - Includes `name`, `description`, and `param_mapping` fields
  - Fixes type checking errors in projects using tool aliases

### Improved
- Release workflow enhancements
  - Added `make changes` command to show commits since last tag
  - Added `make verify-pypi` using RSS feed for instant verification
  - Simplified CLAUDE.md for everyday development focus

## [0.7.4] - 2025-08-11

### Fixed
- Removed unimplemented prompt alias registration code that could cause runtime errors
- Cleaned up TODO comments and disabled code from mcp.py

## [0.7.3] - 2025-08-11

### Added
- MCP tool aliases with parameter remapping support
  - Simple string aliases for alternate tool names
  - Advanced aliases with custom descriptions and parameter mapping
  - Parameter name remapping for semantic clarity (e.g., "command" → "message")
  - Full backward compatibility with existing tools
- Release automation workflow
  - Makefile with standardized release commands
  - Claude command for systematic release process
  - Aligned with tap-tools project patterns

### Fixed
- Fixed bare except in notes_mcp.py example
- Added missing _register_prompt_alias placeholder method

## [0.7.1] - 2025-08-10

### Fixed
- Fixed MCP resource registration error when using optional parameters or Dict types
  - Resources with optional parameters now properly include them in the greedy signature
  - Added missing `params` annotation to wrapper functions for FastMCP compatibility
  - Resolves `KeyError: 'params'` when registering resources with mixed parameter types

### Changed
- Updated `notes_mcp.py` example to use pure JSON-based state for true shared persistence
  - State now reads from JSON on each operation instead of caching in memory
  - Enables proper synchronization between REPL and MCP server instances
  - Added transaction support with rollback capability

## [0.7.0] - 2025-08-10

### Added
- Comprehensive type validation system for MCP compatibility
  - New `validation.py` module with specialized validation functions
  - `strict_types` parameter in `@app.command()` decorator (auto-enabled for MCP)
  - Blocks parameters without type annotations (prevents "unknown" in MCP)
  - Supports nested generics: `List[List[str]]`, `Dict[str, Dict[str, int]]`
  - Rejects Optional[T] and Union[A, B] types that cause "unknown" in MCP clients
  - Clear, actionable error messages at registration time
- Enhanced URI parameter parsing for MCP resources
  - Smart type conversion for all primitive types (int, float, bool, str)
  - List parsing from comma-separated values: `"a,b,c"` → `["a", "b", "c"]`
  - Dict parsing for last parameter: `key1/val1/key2/val2` → `{"key1": "val1", "key2": "val2"}`
  - Type-aware list conversion: `List[int]` properly converts `"1,2,3"` → `[1, 2, 3]`
  - Dash (`-`) placeholder support for using default values
- Resource-specific validation for URI constraints
  - Enforces required parameters before optional ones
  - Validates dict parameters must be last (consume remaining URI segments)
  - Prevents multiple dict parameters in resources

### Changed
- Type validation refactored into separate `validation.py` module
  - Cleaner separation of concerns in `app.py`
  - Reusable validation functions for testing and debugging
  - Better maintainability and extensibility
- MCP resource registration enhanced with parameter ordering validation
  - Resources now validate parameter patterns match URI constraints
  - Better error messages guide developers to correct patterns
  
### Improved
- URI parsing now handles complex types pythonically
  - Lists work with proper type conversion
  - Dict parameters consume remaining segments correctly
  - Empty strings and dashes properly skip to defaults

## [0.6.0] - 2025-08-07

### Added
- Enhanced MCP resource registration with sophisticated parameter handling
  - **All-optional functions**: Dual URI registration (base + template URIs)
  - **Mixed parameters**: Greedy pattern matching with `{params*}` syntax  
  - **Simple functions**: Direct parameter mapping
  - Smart parameter parsing with dash placeholder filtering (`-` values ignored)
- Improved MCP URI generation and stub documentation
  - Enhanced stub URI notation like `/[:param1]/[:param2]` for better API documentation
  - Better greedy parameter handling for flexible MCP resource usage
- MIME-type driven formatting for MCP output
  - Commands with `fastmcp={"mime_type": "text/plain"}` now return formatted ASCII output via MCP
  - Commands with `fastmcp={"mime_type": "application/json"}` return raw JSON data (default behavior)
  - Works for both MCP tools and resources
  - Enables token-efficient formatted output for LLM consumption
- `mime_type` field added to `FastMCPTool` type for consistency with `FastMCPResource`

### Changed  
- Refactored MCP and CLI integration into separate modules for better maintainability
  - No breaking changes to existing public APIs
  - `app.mcp` and `app.cli` properties work exactly the same
  - Sets foundation for future plugin architecture

### Fixed
- Fixed FastMCP `structured_content` validation error for tools with text MIME types
  - Tools with `mime_type="text/*"` now have `output_schema=None` to prevent validation conflicts
  - Resolves "structured_content must be a dict or None" errors for MIME-formatted tools

## [0.5.0] - 2025-01-28

### Added
- Typer CLI integration for traditional command-line interfaces
  - New `typer` parameter in `@app.command()` decorator
  - `TyperConfig` and `TyperDisabled` types for configuration
  - `app.cli()` property for accessing Typer instance
  - Commands automatically work in REPL, CLI, and MCP modes
  - Example: `typer_demo.py` showing todo app with JSON persistence
- Markdown formatter with support for frontmatter and common markdown elements
  - Self-registering markdown element system using `__init_subclass__`
  - `MarkdownElement` base class for creating custom markdown elements
  - `markdown()` builder utility for constructing markdown data structures
  - Core markdown elements: text, heading, code_block, blockquote, list, raw
  - Type-safe implementation with proper annotations

### Fixed
- Consistent None-check patterns in `app.py` for lazy-initialized attributes

## [0.4.0] - 2025-07-25

### Changed
- **BREAKING**: Custom display handlers now receive formatter as third parameter
  - All custom formatters registered with `@app.formatter.register()` must now accept three parameters: `(data, meta, formatter)`
  - This enables proper composition of high-level formatters with low-level textkit functions
  - Migration: Add `formatter` parameter to all custom display handlers
  - See `docs/textkit-architecture.md` for architecture details
- **BREAKING**: Type imports now require explicit module paths
  - `from replkit2.types import CommandMeta` → `from replkit2.types.core import CommandMeta`
  - `from replkit2.types.display import TableData, TreeData, ...` for display types
  - This provides better organization and clearer import statements

### Added
- Formatter instance passed to custom display handlers
- Documentation explaining low-level vs high-level API usage (`docs/textkit-architecture.md`)
- Example demonstrating proper custom formatter implementation (`examples/formatter_demo.py`)
- Type-safe display data validation with `types.display` module
- `ExtensibleFormatter` protocol for formatters with registration capability
- Type annotations for `App.mcp` property returning `FastMCP`
- Enhanced `FastMCPDefaults` with `name` and `description` fields
- `FastMCPDisabled` type for `{"enabled": False}` pattern

### Fixed
- Fixed bug where custom formatters using `table()` directly with `list[dict]` would display keys instead of values
- Custom formatters can now properly reuse formatter logic for data transformation
- Fixed `ExtensibleFormatter` protocol to match actual handler signatures
- Fixed missing type annotations that caused basedpyright errors in dependent projects
- App now correctly types `formatter` parameter as `ExtensibleFormatter`

## [0.3.0]

### Changed
- **BREAKING**: Renamed all `Serializer` classes to `Formatter` throughout the codebase
  - `Serializer` → `Formatter`
  - `TextSerializer` → `TextFormatter`
  - `PassthroughSerializer` → `PassthroughFormatter`
  - `JSONSerializer` → `JSONFormatter`
  - Method `serialize()` → `format()`
  - This better reflects that these components format data for display, not serialize objects

### Added
- Stub resource generation for MCP resources with template URIs
- Custom display component registration example in documentation

### Fixed
- PyDoV4 v3 refactoring for clean data returns and native TextKit displays

## [0.2.0]

### Changed
- Major API refactoring to Flask-style
- Removal of old ReplKit API

### Added
- FastMCP integration for Model Context Protocol support
- Custom display types
- TypedDict support for MCP configurations

## [0.1.0]

### Added
- Initial release
- Flask-style command decorators
- TextKit display system (tables, boxes, trees, charts)
- State management with dataclasses
- PyDoV4 LSP REPL example application