__PROGRAM__ = {
    "name": "Timer",
    "version": "1.0",
    "description": "A simple countdown timer.",
    "params": [
        {"key": "duration", "label": "Duration (seconds)", "type": "int", "required": True, "default": 60, "placeholder": "Enter duration in seconds"},
        {"key": "message", "label": "Completion Message", "type": "str", "required": False, "default": "Time's up!", "placeholder": "Enter a message to display when the timer ends"},
        {"key": "repeat", "label": "Repeat Timer", "type": "bool", "required": False, "default": False, "placeholder": "Should the timer repeat?"}
    ]
}

def run(params: dict) -> str:
    """
    Run the timer with the given parameters.

    Args:
        params (dict): A dictionary containing 'duration', 'message', and 'repeat'.

    Returns:
        str: A message indicating the timer has completed.
    """
    duration = params.get("duration", 60)
    message = params.get("message", "Time's up!")
    repeat = params.get("repeat", False)

    if not isinstance(duration, int) or duration <= 0:
        return "Invalid duration. Please provide a positive integer."
    
    # Simulating timer countdown (not actually waiting)
    countdown_message = f"Timer set for {duration} seconds."
    
    if repeat:
        return f"{countdown_message} It will repeat after completion."
    
    return f"{countdown_message} {message}"