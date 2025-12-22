__PROGRAM__ = {
    "name": "Enhanced Calculator",
    "version": "1.1",
    "description": "An enhanced calculator that performs multiple arithmetic operations and handles edge cases.",
    "params": [
        {
            "key": "operation",
            "label": "Operation",
            "type": "select",
            "required": True,
            "choices": ["add", "subtract", "multiply", "divide", "power", "modulus"],
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

    if operation not in ["add", "subtract", "multiply", "divide", "power", "modulus"]:
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
    elif operation == "power":
        result = num1 ** num2
    elif operation == "modulus":
        if num2 == 0:
            return "Cannot perform modulus by zero."
        result = num1 % num2

    return str(result)

__TESTS__ = [
    {
        "params": {
            "operation": "add",
            "num1": 5,
            "num2": 3
        }
    },
    {
        "params": {
            "operation": "subtract",
            "num1": 10,
            "num2": 4
        }
    },
    {
        "params": {
            "operation": "multiply",
            "num1": 7,
            "num2": 6
        }
    },
    {
        "params": {
            "operation": "divide",
            "num1": 8,
            "num2": 2
        }
    },
    {
        "params": {
            "operation": "divide",
            "num1": 8,
            "num2": 0
        }
    },
    {
        "params": {
            "operation": "power",
            "num1": 2,
            "num2": 3
        }
    },
    {
        "params": {
            "operation": "modulus",
            "num1": 10,
            "num2": 3
        }
    },
    {
        "params": {
            "operation": "modulus",
            "num1": 10,
            "num2": 0
        }
    },
    {
        "params": {
            "operation": "invalid",
            "num1": 10,
            "num2": 5
        }
    },
    {
        "params": {
            "operation": "add",
            "num1": None,
            "num2": 5
        }
    }
]