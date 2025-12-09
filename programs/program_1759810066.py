__PROGRAM__ = {
    "name": "SimpleCalculator",
    "version": "1.1",
    "description": "A simple calculator for basic arithmetic operations.",
    "params": [  # ← ここがスキーマ！
        {
            "key": "operation",
            "label": "演算の種類",
            "type": "select",
            "choices": ["add", "subtract", "multiply", "divide"],
            "default": "add",
            "required": True
        },
        {
            "key": "numbers",
            "label": "数値リスト（カンマ区切り）",
            "type": "list[float]",
            "placeholder": "例: 1,2,3",
            "required": True
        }
    ]
}

def run(params: dict) -> str:
    """Perform basic arithmetic operations."""
    operation = params.get("operation")
    numbers = params.get("numbers", [])
    if not numbers:
        return "Error: numbers list is empty."
    if operation == "add":
        result = sum(numbers)
    elif operation == "subtract":
        result = numbers[0] - sum(numbers[1:])
    elif operation == "multiply":
        result = 1
        for n in numbers:
            result *= n
    elif operation == "divide":
        if 0 in numbers[1:]:
            return "Error: Division by zero."
        result = numbers[0]
        for n in numbers[1:]:
            result /= n
    else:
        return "Error: invalid operation."
    return str(result)