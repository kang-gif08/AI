import jarvis_runtime
__PROGRAM__ = {
    "name": "News Display",
    "version": "1.1",
    "description": "Fetch and display news articles based on a specified topic.",
    "params": [
        {
            "key": "topic",
            "label": "News Topic",
            "type": "str",
            "required": True,
            "placeholder": "Technology"
        },
        {
            "key": "api_key",
            "label": "API Key",
            "type": "str",
            "required": True,
            "placeholder": "Your API Key Here"
        },
        {
            "key": "language",
            "label": "Language",
            "type": "select",
            "required": False,
            "choices": ["en", "es", "fr", "de"],
            "default": "en",
            "placeholder": "Select Language"
        }
    ],
    "kind": "module"
}

def run(params: dict) -> str:
    """Fetch and display news articles based on the specified topic."""
    topic = params.get("topic")
    api_key = params.get("api_key")
    language = params.get("language", "en")

    if not topic or not api_key:
        return "Error: Missing required parameters."

    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={api_key}&language={language}"
    response = jarvis_runtime.http_get_json(url)

    if response.get("status") != "ok":
        return "Error: Unable to fetch news articles."

    articles = response.get("articles", [])
    if not articles:
        return "No articles found."

    news_display = "\n".join(f"{article['title']} - {article['source']['name']}" for article in articles)
    return news_display