from jarvis_runtime import http_get_json

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
            "placeholder": "Enter city name"
        }
    ]
}

def run(params: dict) -> str:
    location = params.get("location")
    api_key = "your_api_key"  # Replace with your actual API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    
    response = http_get_json(url)
    
    if response and response.get("main"):
        temperature = response["main"]["temp"]
        weather_description = response["weather"][0]["description"]
        return f"The current temperature in {location} is {temperature}°C with {weather_description}."
    else:
        return "Could not retrieve weather data. Please check the location and try again."