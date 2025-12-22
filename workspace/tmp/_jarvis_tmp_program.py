import jarvis_runtime

__PROGRAM__ = {
    'name': 'Weather Display',
    'version': '1.0',
    'description': 'Displays the current weather for a specified location.',
    'params': [
        {
            'key': 'location',
            'type': 'string',
            'required': True,
            'placeholder': 'Enter location'
        }
    ],
    'kind': 'utility'
}

def run(params: dict):
    location = params['location']
    api_key = jarvis_runtime.get_secret('weather_api_key')
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
    weather_data = jarvis_runtime.http_get_json(url)
    
    if 'current' in weather_data:
        temperature = weather_data['current']['temp_c']
        condition = weather_data['current']['condition']['text']
        return f"The current temperature in {location} is {temperature}°C with {condition}."
    else:
        return "Could not retrieve weather data."

__TESTS__ = [
    {
        'params': {'location': 'Tokyo'},
        'mock_http_get_json': {
            'current': {
                'temp_c': 20,
                'condition': {'text': 'Clear'}
            }
        }
    },
    {
        'params': {'location': 'New York'},
        'mock_http_get_json': {
            'current': {
                'temp_c': 15,
                'condition': {'text': 'Cloudy'}
            }
        }
    },
    {
        'params': {'location': 'London'},
        'mock_http_get_json': {
            'current': {
                'temp_c': 10,
                'condition': {'text': 'Rain'}
            }
        }
    }
]