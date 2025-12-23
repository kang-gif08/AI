import jarvis_runtime

__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.1",
    "description": "Fetches and displays the current weather for a specified location.",
    "params": [
        {
            "key": "location",
            "label": "Location",
            "type": "str",
            "required": True,
            "placeholder": "Enter a city name"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    location = params['location']
    api_key = jarvis_runtime.get_secret("WEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    
    response = jarvis_runtime.http_get_json(url)
    
    if response and response.get("cod") == 200:
        temperature = response["main"]["temp"]
        weather_description = response["weather"][0]["description"]
        return f"The current temperature in {location} is {temperature}°C with {weather_description}."
    else:
        error_message = response.get("message", "Could not fetch weather data.")
        return f"Error: {error_message}. Please check the location and try again."