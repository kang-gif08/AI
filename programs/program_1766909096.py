import jarvis_runtime

__PROGRAM__ = {
    "name": "Highest Temperature Prefecture",
    "version": "1.0",
    "description": "Displays the prefecture with the highest temperature.",
    "params": [],
}

def run(params: dict):
    url = "https://api.example.com/weather/prefectures"  # Replace with a valid API endpoint
    data = jarvis_runtime.http_get_json(url)
    
    if not data or 'prefectures' not in data:
        return "データが見つかりませんでした。"

    highest_temp_prefecture = max(data['prefectures'], key=lambda x: x['temperature'])
    
    return f"一番気温の高い都道府県は {highest_temp_prefecture['name']} で、気温は {highest_temp_prefecture['temperature']}度です。"