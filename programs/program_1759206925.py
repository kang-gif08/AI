__PROGRAM__ = {
    "name": "DateTimeWeatherDisplay",
    "version": "1.0",
    "description": "Displays the current date, time, and weather status."
}

from datetime import datetime

def run(params: dict) -> str:
    """Returns the current date and time formatted as YYYY-MM-DD HH:MM:SS and the weather status."""
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weather_status = params.get("weather", "No weather data available.")
    return f"{current_datetime} - Weather: {weather_status}"