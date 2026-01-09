import jarvis_runtime
from datetime import datetime, timedelta

__PROGRAM__ = {
    "name": "Date Calculator",
    "version": "1.0",
    "description": "Calculates future or past dates based on input days.",
    "params": [
        {
            "key": "days",
            "label": "Days to add/subtract",
            "type": "int",
            "required": True,
            "default": 0,
            "placeholder": "Enter number of days"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    days = params.get("days", 0)
    current_date = datetime.now()
    calculated_date = current_date + timedelta(days=days)
    return calculated_date.strftime("%Y-%m-%d")