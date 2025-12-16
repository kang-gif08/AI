import jarvis_runtime
__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.0",
    "description": "Fetch and display weather information for a specified city.",
    "params": [
        {
            "key": "city",
            "label": "City Name",
            "type": "str",
            "required": True,
            "placeholder": "Tokyo"
        },
        {
            "key": "api_key",
            "label": "API Key",
            "type": "str",
            "required": True,
            "placeholder": "Your API Key"
        }
    ],
    "kind": "module"
}

def run(params: dict) -> str:
    """Fetch and display weather information for the specified city."""
    city = params.get("city")
    api_key = params.get("api_key")
    
    if not city or not api_key:
        return "City and API Key are required parameters."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = jarvis_runtime.http_get_json(url)

    if response.get("cod") != 200:
        return f"Error fetching weather data: {response.get('message', 'Unknown error')}"

    weather = response.get("weather", [{}])[0].get("description", "No description available.")
    temperature = response.get("main", {}).get("temp", "No temperature data available.")
    
    return f"The weather in {city} is currently {weather} with a temperature of {temperature}°C."