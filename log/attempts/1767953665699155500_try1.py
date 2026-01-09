import jarvis_runtime

__PROGRAM__ = {
    "name": "NewsFetcher",
    "version": "1.0",
    "description": "Fetches news articles based on the specified field of interest.",
    "params": [
        {
            "key": "field",
            "label": "Field of Interest",
            "type": "str",
            "required": True,
            "placeholder": "e.g., Technology, Health, Sports"
        },
        {
            "key": "num_articles",
            "label": "Number of Articles",
            "type": "int",
            "required": True,
            "default": 5
        }
    ],
    "kind": "module"
}

def run(params: dict):
    field = params['field']
    num_articles = params['num_articles']
    
    # Simulate fetching news articles based on the field
    news_api_url = f"https://newsapi.org/v2/everything?q={field}&pageSize={num_articles}&apiKey={jarvis_runtime.get_secret('NEWS_API_KEY')}"
    news_data = jarvis_runtime.http_get_json(news_api_url)
    
    articles = news_data.get('articles', [])
    news_summary = []
    
    for article in articles:
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        news_summary.append(f"{title}: {url}")
    
    return "\n".join(news_summary) if news_summary else "No articles found."