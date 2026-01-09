import jarvis_runtime

__PROGRAM__ = {
    "name": "Unit Converter",
    "version": "1.0",
    "description": "A tool to convert between length, weight, and temperature units.",
    "params": [
        {
            "key": "category",
            "label": "Category",
            "type": "select",
            "required": True,
            "choices": ["length", "weight", "temp"],
            "placeholder": "Select a category"
        },
        {
            "key": "value",
            "label": "Value",
            "type": "float",
            "required": True,
            "placeholder": "Enter the value to convert"
        },
        {
            "key": "from_unit",
            "label": "From Unit",
            "type": "str",
            "required": True,
            "placeholder": "Enter the unit to convert from"
        },
        {
            "key": "to_unit",
            "label": "To Unit",
            "type": "str",
            "required": True,
            "placeholder": "Enter the unit to convert to"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    category = params['category']
    value = params['value']
    from_unit = params['from_unit']
    to_unit = params['to_unit']

    conversion_factors = {
        'length': {
            'meters': 1,
            'kilometers': 0.001,
            'miles': 0.000621371,
            'feet': 3.28084,
            'inches': 39.3701
        },
        'weight': {
            'grams': 1,
            'kilograms': 0.001,
            'pounds': 0.00220462,
            'ounces': 0.035274
        },
        'temp': {
            'celsius': lambda x: x,
            'fahrenheit': lambda x: (x * 9/5) + 32,
            'kelvin': lambda x: x + 273.15
        }
    }

    if category in ['length', 'weight']:
        if from_unit not in conversion_factors[category] or to_unit not in conversion_factors[category]:
            return "Invalid units for the selected category."
        
        base_value = value * conversion_factors[category][from_unit]
        converted_value = base_value / conversion_factors[category][to_unit]
        return f"{value} {from_unit} is equal to {converted_value} {to_unit}."

    elif category == 'temp':
        if from_unit not in conversion_factors['temp'] or to_unit not in conversion_factors['temp']:
            return "Invalid units for temperature conversion."
        
        if from_unit == 'celsius':
            base_value = value
        else:
            base_value = conversion_factors['temp'][from_unit](value)

        if to_unit == 'celsius':
            converted_value = base_value
        else:
            converted_value = conversion_factors['temp'][to_unit](base_value)

        return f"{value} {from_unit} is equal to {converted_value} {to_unit}."

    return "Invalid category."