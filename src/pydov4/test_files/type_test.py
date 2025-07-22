"""Test file for type-checking with basedpyright/pyright.

This file contains various type-related issues.
"""

from typing import List, Dict, Optional, Union, Any


# Test 1: Missing type annotations
def add_numbers(a, b):  # Missing parameter types and return type
    return a + b


# Test 2: Type mismatch
def process_string(text: str) -> int:
    return text  # Type error: returning str instead of int


# Test 3: Undefined variable
def use_undefined():
    print(undefined_variable)  # Name error: undefined variable
    return result  # Another undefined variable


# Test 4: Missing return
def missing_return(value: int) -> str:
    if value > 0:
        return "positive"
    # Missing return for else case


# Test 5: Optional not handled
def handle_optional(value: Optional[str]) -> int:
    return len(value)  # Type error: value could be None


# Test 6: Wrong argument types
def typed_function(x: int, y: str) -> str:
    return f"{x}: {y}"

result = typed_function("hello", 123)  # Arguments swapped


# Test 7: List type issues
def process_list(items: List[int]) -> List[str]:
    return items  # Type error: returning List[int] instead of List[str]


# Test 8: Dict type issues
def get_config() -> Dict[str, int]:
    return {
        "timeout": 30,
        "retries": "three",  # Type error: str instead of int
        "port": 8080
    }


# Test 9: Class with missing annotations
class DataProcessor:
    def __init__(self):
        self.data = []  # Missing type annotation
        self.count = 0  # Missing type annotation
    
    def add_item(self, item):  # Missing parameter and return types
        self.data.append(item)
        self.count += 1
    
    def get_total(self):  # Missing return type
        return self.count


# Test 10: Generic type issues
def first_element(items: List) -> Any:  # List without type parameter
    if items:
        return items[0]
    return None


# Test 11: Union type not handled properly
def process_input(value: Union[str, int]) -> str:
    return value.upper()  # Type error: int has no upper() method


# Test 12: Incompatible override
class Base:
    def method(self, x: int) -> str:
        return str(x)


class Derived(Base):
    def method(self, x: str) -> int:  # Incompatible override
        return int(x)