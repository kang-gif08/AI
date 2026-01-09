import jarvis_runtime

__PROGRAM__ = {
    "name": "BMI and Calorie Calculator",
    "version": "1.0",
    "description": "Calculate BMI, standard weight, and daily calorie target based on height, weight, activity level, and goal.",
    "params": [
        {"key": "height", "label": "Height (cm)", "type": "float", "required": True, "placeholder": "Enter height in cm"},
        {"key": "weight", "label": "Weight (kg)", "type": "float", "required": True, "placeholder": "Enter weight in kg"},
        {"key": "activity_level", "label": "Activity Level", "type": "select", "required": True, "choices": ["sedentary", "light", "moderate", "active"], "placeholder": "Select activity level"},
        {"key": "goal", "label": "Goal", "type": "select", "required": True, "choices": ["maintain", "lose", "gain"], "placeholder": "Select your goal"}
    ],
    "kind": "module"
}

def run(params: dict):
    height = params['height'] / 100  # Convert cm to meters
    weight = params['weight']
    
    # Calculate BMI
    bmi = weight / (height ** 2)
    
    # Calculate standard weight (ideal weight)
    standard_weight = 22 * (height ** 2)
    
    # Calculate daily calorie needs based on activity level
    if params['activity_level'] == "sedentary":
        activity_multiplier = 1.2
    elif params['activity_level'] == "light":
        activity_multiplier = 1.375
    elif params['activity_level'] == "moderate":
        activity_multiplier = 1.55
    else:  # active
        activity_multiplier = 1.725
    
    # Basal Metabolic Rate (BMR) estimation using Mifflin-St Jeor Equation for men
    bmr = 10 * weight + 6.25 * (height * 100) - 5 * 30 + 5  # Assuming age 30 for calculation
    
    # Total Daily Energy Expenditure (TDEE)
    tdee = bmr * activity_multiplier
    
    # Adjust TDEE based on goal
    if params['goal'] == "lose":
        calorie_target = tdee - 500  # Deficit for weight loss
    elif params['goal'] == "gain":
        calorie_target = tdee + 500  # Surplus for weight gain
    else:  # maintain
        calorie_target = tdee
    
    return {
        "BMI": round(bmi, 2),
        "Standard Weight (kg)": round(standard_weight, 2),
        "Daily Calorie Target": round(calorie_target)
    }