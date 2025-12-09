from jarvis_runtime import http_get_json

__PROGRAM__ = {
    "name": "TokyoWeatherFetcher",
    "version": "1.1",
    "description": "Fetches current weather in Tokyo.",
    "params": [
        {
            "key": "api_key",
            "label": "API Key",
            "type": "str",
            "required": True,
            "placeholder": "Enter your OpenWeatherMap API key"
        }
    ]
}

def run(params: dict) -> str:
    """Fetch current weather for Tokyo and return readable text."""
    api_key = params["api_key"]
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid={api_key}&units=metric"
    
    response = http_get_json(url)

    if "main" in response and "weather" in response:
        temp = response["main"]["temp"]
        desc = response["weather"][0]["description"]
        return f"Tokyo Weather:\n- Temperature: {temp} °C\n- Condition: {desc}"
    else:
        return f"Error: {response}"