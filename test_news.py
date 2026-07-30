from services.news.news_service import NewsService

service = NewsService()

news = service.get_news("tr")

for article in news:
    print(article["title"])
    