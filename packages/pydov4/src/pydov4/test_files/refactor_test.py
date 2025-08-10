"""Test file for refactoring operations.

This file contains code that can be refactored in various ways.
"""


# Test 1: Extract variable opportunity
def calculate_price():
    total = 100 * 1.2 * 0.9  # Could extract tax and discount rates
    return total


# Test 2: Extract method opportunity
def process_data(data):
    # Validation logic that could be extracted
    if not data:
        raise ValueError("Data is empty")
    if not isinstance(data, list):
        raise TypeError("Data must be a list")
    if len(data) > 1000:
        raise ValueError("Data too large")
    
    # Processing logic
    result = []
    for item in data:
        result.append(item * 2)
    return result


# Test 3: Rename opportunities
def calc(x, y):  # Poor function name
    res = x + y  # Poor variable name
    return res


# Test 4: Inline variable opportunity
def get_message(name):
    greeting = f"Hello, {name}"
    return greeting  # Could inline


# Test 5: Class that could use property
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius
    
    def get_fahrenheit(self):  # Could be a property
        return self.celsius * 9/5 + 32
    
    def set_fahrenheit(self, f):  # Could be a property setter
        self.celsius = (f - 32) * 5/9