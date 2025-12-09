__PROGRAM__ = {
    "name": "WeatherFetcher",
    "version": "1.2",
    "description": "Fetch today's weather information.",
    "params": [
        {
            "key": "city",
            "label": "City",
            "type": "str",
            "required": True,
            "placeholder": "Enter the city name"
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
    "kind": "utility"
}

def run(params: dict) -> str:
    from jarvis_runtime import read_text, http_get_json

    city = params["city"]
    unit = params["unit"]
    
    # Load API key and base URL from config.py
    config_content = read_text("config.py")
    config = {}
    exec(config_content, config)
    
    api_key = config.get("API_KEY")
    base_url = config.get("BASE_URL", "http://api.openweathermap.org/data/2.5/weather")

    url = f"{base_url}?q={city}&units={unit}&appid={api_key}"

    response = http_get_json(url)
    if response and response.get("cod") == 200:
        weather_description = response["weather"][0]["description"]
        temperature = response["main"]["temp"]
        return f"Today's weather in {city}: {weather_description} with a temperature of {temperature}°."
    else:
        return "Failed to fetch weather data. Please check the city name."