__PROGRAM__ = {
    "name": "SimpleCalculator",
    "version": "1.1",
    "description": "A simple calculator for basic arithmetic operations with multiple numbers.",
    "params": [
        {"key": "operation", "label": "Operation", "type": "select", "required": True, "choices": ["add", "subtract", "multiply", "divide"], "placeholder": "Select operation"},
        {"key": "numbers", "label": "Numbers", "type": "list[float]", "required": True, "placeholder": "Enter numbers separated by commas"}
    ]
}

def run(params: dict) -> str:
    """Perform a basic arithmetic operation on a list of numbers based on the provided parameters."""
    operation = params.get("operation")
    numbers = params.get("numbers")

    if operation not in {"add", "subtract", "multiply", "divide"}:
        return "Invalid operation."

    if not numbers or any(num is None for num in numbers):
        return "Numbers cannot be None or empty."

    if operation == "add":
        return str(sum(numbers))
    elif operation == "subtract":
        return str(numbers[0] - sum(numbers[1:]))
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

    return "Invalid parameters."