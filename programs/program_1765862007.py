__PROGRAM__ = {
    "name": "Simple Calculator",
    "version": "1.0",
    "description": "A simple calculator that performs basic arithmetic operations.",
    "params": [
        {
            "key": "operation",
            "label": "Operation",
            "type": "select",
            "required": True,
            "choices": ["add", "subtract", "multiply", "divide"],
            "placeholder": "add"
        },
        {
            "key": "num1",
            "label": "First Number",
            "type": "float",
            "required": True,
            "placeholder": "0.0"
        },
        {
            "key": "num2",
            "label": "Second Number",
            "type": "float",
            "required": True,
            "placeholder": "0.0"
        }
    ],
    "kind": "module"
}

def run(params: dict) -> str:
    """Executes the calculator operation based on provided parameters."""
    operation = params.get("operation")
    num1 = params.get("num1")
    num2 = params.get("num2")

    if operation not in ["add", "subtract", "multiply", "divide"]:
        return "Invalid operation."

    if num1 is None or num2 is None:
        return "Both numbers are required."

    if operation == "add":
        result = num1 + num2
    elif operation == "subtract":
        result = num1 - num2
    elif operation == "multiply":
        result = num1 * num2
    elif operation == "divide":
        if num2 == 0:
            return "Cannot divide by zero."
        result = num1 / num2

    return str(result)