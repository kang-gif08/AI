import jarvis_runtime

__PROGRAM__ = {
    "name": "NewsFetcher",
    "version": "1.1",
    "description": "日本の最新ニュース記事を取得します。",
    "params": [],
    "kind": "module"
}

def run(params: dict):
    news_api_url = "https://newsapi.org/v2/top-headlines?country=jp&apiKey=" + jarvis_runtime.get_secret("NEWS_API_KEY")
    news_data = jarvis_runtime.http_get_json(news_api_url)
    
    articles = news_data.get("articles", [])
    if not articles:
        return "ニュース記事が見つかりませんでした。"

    news_summary = []
    for article in articles:
        title = article.get("title", "タイトルなし")
        description = article.get("description", "説明なし")
        news_summary.append(f"タイトル: {title}\n説明: {description}\n")

    return "\n".join(news_summary)