import jarvis_runtime
import requests

__PROGRAM__ = {
    "name": "City Temperature Ranking",
    "version": "1.0",
    "description": "Fetch current temperatures for multiple cities and rank them in ascending order.",
    "params": [
        {
            "key": "cities",
            "label": "Cities",
            "type": "list[str]",
            "required": True,
            "placeholder": "Enter city names"
        }
    ],
    "kind": "module"
}

def run(params: dict):
    cities = params['cities']
    api_key = jarvis_runtime.get_secret("WEATHER_API_KEY")
    temperatures = {}
    errors = {}

    for city in cities:
        try:
            response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
            response.raise_for_status()
            data = response.json()
            temperatures[city] = data['main']['temp']
        except requests.exceptions.HTTPError as e:
            errors[city] = str(e)
        except Exception as e:
            errors[city] = f"An error occurred: {str(e)}"

    sorted_temperatures = sorted(temperatures.items(), key=lambda x: x[1])
    result = {city: temp for city, temp in sorted_temperatures}

    if errors:
        result['errors'] = errors

    return result