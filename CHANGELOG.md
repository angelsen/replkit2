# Changelog

All notable changes to ReplKit2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.3.0] - 2025-01-22

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

## [0.2.0] - 2025-01-21

### Changed
- Major API refactoring to Flask-style
- Removal of old ReplKit API

### Added
- FastMCP integration for Model Context Protocol support
- Custom display types
- TypedDict support for MCP configurations

## [0.1.0] - 2025-01-01

### Added
- Initial release
- Flask-style command decorators
- TextKit display system (tables, boxes, trees, charts)
- State management with dataclasses
- PyDoV4 LSP REPL example application