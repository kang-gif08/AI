import jarvis_runtime

__PROGRAM__ = {
    "name": "NewsFetcher",
    "version": "1.0",
    "description": "Fetches the latest news articles.",
    "params": [],
    "kind": "module"
}

def run(params: dict):
    url = "https://newsapi.org/v2/top-headlines?country=jp&apiKey=" + jarvis_runtime.get_secret("NEWS_API_KEY")
    news_data = jarvis_runtime.http_get_json(url)
    
    articles = news_data.get("articles", [])
    news_summary = []
    
    for article in articles:
        title = article.get("title", "No title")
        description = article.get("description", "No description")
        news_summary.append(f"Title: {title}\nDescription: {description}\n")
    
    return "\n".join(news_summary) if news_summary else "No news available."