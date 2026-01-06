import jarvis_runtime

__PROGRAM__ = {
    "name": "HighestTemperaturePrefecture",
    "version": "1.0",
    "description": "Displays the prefecture with the highest temperature.",
    "params": [],
}

def run(params: dict):
    url = "https://api.example.com/temperature_data"  # Replace with actual API endpoint
    data = jarvis_runtime.http_get_json(url)
    
    highest_temp_prefecture = max(data, key=lambda x: x['temperature'])
    
    return highest_temp_prefecture['prefecture']