# ReplKit2 Development Guide

## Type Checking Philosophy

This project uses basedpyright with a pragmatic approach. We prioritize readable, maintainable code over perfect type coverage.

### Be explicit about type checking goals

**Less effective:**
```
Fix all type warnings
```

**More effective:**
```
Fix type errors that could cause runtime bugs. For warnings, only fix those that improve code clarity. Accept that dynamic Python patterns (like decorator registration) will generate warnings.
```

### Add context for type decisions

**Less effective:**
```
Use Any type
```

**More effective:**
```
The serializer handles arbitrary user data that can be strings, numbers, lists, or dicts. Using `Any` here accurately reflects the dynamic nature of the data and keeps the code simple.
```

## Common Patterns

### Decorator-registered functions
Functions registered via decorators appear unused to static analysis. Add `# pyright: ignore[reportUnusedFunction]` to acknowledge this pattern.

### Dynamic data handling
When a function genuinely handles any type of data (like our display serializers), use `Any` rather than complex union types that add no safety.

### Override methods
If you're not using Python 3.12's `@override` decorator, add `# pyright: ignore[reportImplicitOverride]` to overriding methods.

## Running Type Checks

```bash
# Full project check
uv run basedpyright

# Single file check  
uv run basedpyright src/replkit2/textkit/serializer.py

# Generate JSON report for analysis
uv run basedpyright --outputjson > pyright_report.json
```

## Making Type Decisions

When encountering type warnings, ask:
1. Does fixing this prevent actual bugs?
2. Does the fix make the code clearer?
3. Does the fix require type gymnastics?

If you answered "no, no, yes" - use a targeted `pyright: ignore` comment instead.