# Changelog

All notable changes to ReplKit2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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