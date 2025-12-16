__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.0",
    "description": "Fetch and display weather information for a specified location.",
    "params": [
        {
            "key": "location",
            "label": "Location",
            "type": "str",
            "required": True,
            "placeholder": "Enter a city name"
        },
        {
            "key": "unit",
            "label": "Unit",
            "type": "select",
            "required": True,
            "choices": ["metric", "imperial"],
            "default": "metric"
        }
    ],
    "kind": "project_generator"
}

def run(params: dict) -> dict[str, str]:
    location = params["location"]
    unit = params["unit"]
    api_key = "your_api_key_here"  # Replace with your actual API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&units={unit}&appid={api_key}"
    
    weather_data = http_get_json(url)
    
    if "main" in weather_data:
        temp = weather_data["main"]["temp"]
        weather_description = weather_data["weather"][0]["description"]
        result = f"The current temperature in {location} is {temp}° with {weather_description}."
    else:
        result = "Could not retrieve weather data. Please check the location."
    
    return {"output": result}