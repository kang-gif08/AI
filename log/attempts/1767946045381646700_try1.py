import jarvis_runtime

__PROGRAM__ = {
    "name": "Habit Tracker",
    "version": "1.0",
    "description": "Track the days a habit was performed and calculate the streak and monthly count.",
    "params": [
        {
            "key": "habit_name",
            "label": "Habit Name",
            "type": "str",
            "required": True,
            "placeholder": "e.g., 筋トレ or 勉強"
        },
        {
            "key": "date",
            "label": "Date of Execution",
            "type": "str",
            "required": True,
            "placeholder": "YYYY-MM-DD"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    habit_name = params['habit_name']
    date = params['date']
    
    # Read existing habit records
    try:
        records = jarvis_runtime.read_json('habit_records.json')
    except FileNotFoundError:
        records = {}

    # Initialize habit record if not present
    if habit_name not in records:
        records[habit_name] = []

    # Add the new date if not already recorded
    if date not in records[habit_name]:
        records[habit_name].append(date)

    # Sort dates and calculate streak
    records[habit_name].sort()
    streak = 0
    monthly_count = 0
    current_date = jarvis_runtime.datetime.datetime.strptime(date, "%Y-%m-%d").date()
    month_start = current_date.replace(day=1)

    # Calculate streak
    for record_date in reversed(records[habit_name]):
        record_date_obj = jarvis_runtime.datetime.datetime.strptime(record_date, "%Y-%m-%d").date()
        if (current_date - record_date_obj).days == streak:
            streak += 1
        else:
            break

    # Calculate monthly count
    for record_date in records[habit_name]:
        record_date_obj = jarvis_runtime.datetime.datetime.strptime(record_date, "%Y-%m-%d").date()
        if record_date_obj >= month_start:
            monthly_count += 1

    # Save updated records
    jarvis_runtime.write_json('habit_records.json', records)

    return f"Habit: {habit_name}, Streak: {streak}, Monthly Count: {monthly_count}"