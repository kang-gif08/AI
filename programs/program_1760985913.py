__PROGRAM__ = {
    "name": "SimpleCalculator",
    "version": "1.3",
    "description": "A simple calculator that performs basic arithmetic operations on multiple numbers, including the ability to add or subtract a constant, and allows for intermediate calculations.",
    "params": [
        {"key": "operation", "label": "Operation", "type": "select", "required": True, "choices": ["add", "subtract", "multiply", "divide", "intermediate"], "placeholder": "Select an operation"},
        {"key": "numbers", "label": "Numbers", "type": "list[float]", "required": True, "placeholder": "Enter numbers separated by commas"},
        {"key": "constant", "label": "Constant", "type": "float", "required": False, "default": 0.0, "placeholder": "Enter a constant to add or subtract"},
        {"key": "intermediate_result", "label": "Intermediate Result", "type": "float", "required": False, "placeholder": "Enter a previous result for intermediate calculations"}
    ]
}

def run(params: dict) -> str:
    """
    Perform a calculation based on the provided parameters.

    Args:
        params (dict): A dictionary containing 'operation', 'numbers', an optional 'constant', and an optional 'intermediate_result'.

    Returns:
        str: The result of the calculation or an error message.
    """
    operation = params.get("operation")
    numbers = params.get("numbers")
    constant = params.get("constant", 0.0)
    intermediate_result = params.get("intermediate_result", None)

    if operation not in ["add", "subtract", "multiply", "divide", "intermediate"]:
        return "Invalid operation."

    if not numbers or any(num is None for num in numbers):
        return "Numbers are required."

    if operation == "add":
        return str(sum(numbers) + constant)
    elif operation == "subtract":
        return str(numbers[0] - sum(numbers[1:]) - constant)
    elif operation == "multiply":
        result = 1
        for num in numbers:
            result *= num
        return str(result)
    elif operation == "divide":
        if any(num == 0 for num in numbers[1:]):
            return "Cannot divide by zero."
        result = numbers[0]
        for num in numbers[1:]:
            result /= num
        return str(result)
    elif operation == "intermediate":
        if intermediate_result is None:
            return "Intermediate result is required for this operation."
        return str(intermediate_result + sum(numbers) + constant)

__PARAMS_SCHEMA__ = __PROGRAM__["params"]