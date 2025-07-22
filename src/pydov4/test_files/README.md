# PyDoV4 Test Files

This directory contains test files for testing PyDoV4's LSP functionality with different language servers.

## Files

### ruff_test.py
Tests for Ruff-specific code actions:
- Unused import removal
- Import sorting
- Style fixes (is None, f-strings, etc.)
- Whitespace issues
- Line length violations
- Common linting issues

### type_test.py
Tests for type checkers (basedpyright, pyright, pylsp):
- Missing type annotations
- Type mismatches
- Undefined variables
- Missing returns
- Optional handling
- Generic type issues
- Class typing

### clean_test.py
A clean file with no issues for testing:
- Basic file operations
- Edit/save functionality
- Baseline for comparisons

### refactor_test.py
Tests for refactoring operations:
- Extract variable/method
- Rename symbols
- Inline operations
- Code improvements

## Usage

```python
# In PyDoV4 REPL
connect('ruff')
open('src/pydov4/test_files/ruff_test.py')
diagnostics()
actions()

# Test with different servers
connect('basedpyright')
open('src/pydov4/test_files/type_test.py')
diagnostics()
```

## Testing Code Actions

To investigate what different servers return:

```python
# Get the state object
state = app._state

# Get code actions directly
actions = state.client.code_actions(state.current_file, line, col)

# Apply and see the raw result
result = state.client.apply_code_action(actions[0])
print(result)
```