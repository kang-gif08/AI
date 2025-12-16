import jarvis_runtime
__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.0",
    "description": "Fetches and displays the current weather for a specified location.",
    "params": [
        {
            "key": "location",
            "label": "Location",
            "type": "str",
            "required": True,
            "placeholder": "Enter a city name"
        },
        {
            "key": "api_key",
            "label": "API Key",
            "type": "str",
            "required": True,
            "placeholder": "Enter your weather API key"
        }
    ],
    "kind": "module"
}

def run(params: dict) -> str:
    """
    Fetches the current weather for the specified location using the provided API key.

    Args:
        params (dict): A dictionary containing 'location' and 'api_key'.

    Returns:
        str: A string describing the current weather.
    """
    location = params.get("location")
    api_key = params.get("api_key")

    if not location or not api_key:
        return "Location and API key are required."

    # Construct the API URL
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

    # Fetch the weather data
    response = jarvis_runtime.http_get_json(url)
    
    if response.get("cod") != 200:
        return f"Error fetching weather data: {response.get('message', 'Unknown error')}"

    # Extract relevant information
    weather_description = response["weather"][0]["description"]
    temperature = response["main"]["temp"]
    
    return f"The current weather in {location} is {weather_description} with a temperature of {temperature}°C."