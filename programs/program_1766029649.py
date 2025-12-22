__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.0",
    "description": "Fetch and display the current weather for a specified location.",
    "params": ["location"],
    "kind": "module"
}

def run(params: dict) -> str:
    """
    Fetch and display the current weather for the specified location.

    Args:
        params (dict): A dictionary containing the user input.
                        Expected keys: 'location' (str)

    Returns:
        str: A message containing the weather information or an error message.
    """
    location = params.get("location")
    
    if not location:
        return "Error: Location parameter is required."

    # Fetch weather data from an external API
    api_key = jarvis_runtime.get_secret("WEATHER_API_KEY")
    url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

    weather_data = jarvis_runtime.http_get_json(url)

    if "error" in weather_data:
        return f"Error: {weather_data['error']['message']}"

    current_weather = weather_data["current"]
    temperature = current_weather["temp_c"]
    condition = current_weather["condition"]["text"]

    return f"The current temperature in {location} is {temperature}°C with {condition}."