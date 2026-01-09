import jarvis_runtime

__PROGRAM__ = {
    "name": "Progress Rate Calculator",
    "version": "1.0",
    "description": "Calculate progress rate and remaining estimates based on total tasks and completed tasks.",
    "params": [
        {
            "key": "total_tasks",
            "label": "Total Tasks",
            "type": "int",
            "required": True,
            "placeholder": "Enter total number of tasks"
        },
        {
            "key": "completed_tasks",
            "label": "Completed Tasks",
            "type": "int",
            "required": True,
            "placeholder": "Enter number of completed tasks"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    total_tasks = params['total_tasks']
    completed_tasks = params['completed_tasks']
    
    if total_tasks <= 0:
        return "Total tasks must be greater than zero."
    
    progress_rate = (completed_tasks / total_tasks) * 100
    remaining_tasks = total_tasks - completed_tasks
    
    return f"Progress Rate: {progress_rate:.2f}%, Remaining Tasks: {remaining_tasks}"