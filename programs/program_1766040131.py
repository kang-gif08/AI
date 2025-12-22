__PROGRAM__ = {
    "name": "Weather Display",
    "version": "1.0",
    "description": "A program to display the current weather information.",
    "params": [
        {
            "key": "city",
            "type": "string",
            "required": True
        },
        {
            "key": "unit",
            "type": "string",
            "required": False
        }
    ],
    "kind": "utility"
}

def run(params: dict):
    import requests

    city = params.get("city")
    unit = params.get("unit", "metric")  # Default to metric if not provided

    api_key = "your_api_key_here"  # Replace with your actual API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units={unit}&appid={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        main = weather_data['main']
        weather = weather_data['weather'][0]
        temperature = main['temp']
        description = weather['description']
        return {
            "temperature": temperature,
            "description": description
        }
    else:
        return {
            "error": "Could not retrieve weather data."
        }