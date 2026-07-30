from services.news.news_service import NewsService
from services.news.ranking.category_classifier import CategoryClassifier

service = NewsService()

articles = service.get_turkey_news()

classifier = CategoryClassifier()

for article in articles[:30]:

    category = classifier.classify(article)

    print(f"[{category.value}] {article.title}")