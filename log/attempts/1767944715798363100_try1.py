import jarvis_runtime

__PROGRAM__ = {
    "name": "BMI and Calorie Calculator",
    "version": "1.0",
    "description": "Calculate BMI, standard weight, and daily calorie goals based on height, weight, activity level, and purpose.",
    "params": [
        {"key": "height", "label": "Height (cm)", "type": "float", "required": True, "placeholder": "e.g., 170"},
        {"key": "weight", "label": "Weight (kg)", "type": "float", "required": True, "placeholder": "e.g., 70"},
        {"key": "activity_level", "label": "Activity Level", "type": "select", "required": True, 
         "choices": ["sedentary", "light", "moderate", "active", "very active"], "placeholder": "Select activity level"},
        {"key": "goal", "label": "Goal", "type": "select", "required": True, 
         "choices": ["maintain", "lose", "gain"], "placeholder": "Select your goal"}
    ],
    "kind": "module"
}

def run(params: dict):
    height = params['height']
    weight = params['weight']
    activity_level = params['activity_level']
    goal = params['goal']

    # Calculate BMI
    bmi = weight / ((height / 100) ** 2)

    # Calculate standard weight (ideal weight range)
    standard_weight = 22 * ((height / 100) ** 2)

    # Calculate daily calorie needs based on activity level
    if activity_level == "sedentary":
        calorie_multiplier = 1.2
    elif activity_level == "light":
        calorie_multiplier = 1.375
    elif activity_level == "moderate":
        calorie_multiplier = 1.55
    elif activity_level == "active":
        calorie_multiplier = 1.725
    else:  # very active
        calorie_multiplier = 1.9

    # Basal Metabolic Rate (BMR) calculation (Mifflin-St Jeor Equation for men)
    bmr = 10 * weight + 6.25 * height - 5 * 30 + 5  # Assuming age is 30 for simplicity

    # Total Daily Energy Expenditure (TDEE)
    tdee = bmr * calorie_multiplier

    # Adjust for goal
    if goal == "lose":
        daily_calories = tdee - 500  # 500 calorie deficit for weight loss
    elif goal == "gain":
        daily_calories = tdee + 500  # 500 calorie surplus for weight gain
    else:
        daily_calories = tdee  # Maintain weight

    return {
        "BMI": round(bmi, 2),
        "Standard Weight (kg)": round(standard_weight, 2),
        "Daily Calorie Goal": round(daily_calories, 2)
    }