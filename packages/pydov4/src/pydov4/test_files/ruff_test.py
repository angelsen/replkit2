"""Test file for Ruff code actions.

This file contains various style and linting issues that Ruff can fix.
"""

# Test 1: Unused imports (for organize imports action)
import json
import os
import sys
from typing import List, Dict, Optional
import datetime
import re


# Test 2: Unsorted imports (Ruff will sort them)
import requests
import ast
import collections


# Test 3: Used imports (should not be removed)
import math


def calculate_circle_area(radius: float) -> float:
    """Calculate area using math.pi."""
    return math.pi * radius ** 2


# Test 4: Comparison with None (should use 'is')
def check_none(value):
    if value == None:  # E711: Should use 'is None'
        return True
    elif value != None:  # E711: Should use 'is not None'
        return False
    return None


# Test 5: F-string without placeholders
def get_static_message():
    message = f"This has no placeholders"  # F541: f-string without placeholders
    return message


# Test 6: Trailing whitespace
def trailing_spaces():    
    """This line has trailing spaces."""    
    pass    


# Test 7: Missing blank lines between functions
def function_one():
    pass
def function_two():
    pass


# Test 8: Line too long
def very_long_line():
    extremely_long_variable_name = "This is a really really really really really really really really really really really long string that definitely exceeds the maximum line length"
    return extremely_long_variable_name


# Test 9: Mutable default argument
def append_to_list(item, target_list=[]):  # B006: Mutable default argument
    target_list.append(item)
    return target_list


# Test 10: Unnecessary else after return
def unnecessary_else(value):
    if value > 0:
        return "positive"
    else:  # RET505: Unnecessary else after return
        return "non-positive"