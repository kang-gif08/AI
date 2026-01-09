import jarvis_runtime

__PROGRAM__ = {
    "name": "Calculator",
    "version": "1.0",
    "description": "A simple calculator that performs basic arithmetic operations.",
    "params": [
        {"key": "operation", "label": "Operation", "type": "select", "required": True,
         "choices": ["add", "subtract", "multiply", "divide"], "placeholder": "Select an operation"},
        {"key": "num1", "label": "First Number", "type": "float", "required": True},
        {"key": "num2", "label": "Second Number", "type": "float", "required": True}
    ],
    "kind": "module"
}

def run(params: dict):
    operation = params['operation']
    num1 = params['num1']
    num2 = params['num2']
    
    if operation == "add":
        result = num1 + num2
    elif operation == "subtract":
        result = num1 - num2
    elif operation == "multiply":
        result = num1 * num2
    elif operation == "divide":
        if num2 == 0:
            return "Error: Division by zero is not allowed."
        result = num1 / num2
    else:
        return "Error: Invalid operation."
    
    return f"The result of {operation}ing {num1} and {num2} is {result}."