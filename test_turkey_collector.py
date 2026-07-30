from collections import Counter

from services.news.news_service import NewsService

service = NewsService()

articles = service.get_turkey_news()

print(f"Toplam haber: {len(articles)}")

counter = Counter(article.source for article in articles)

print("\nKaynak dağılımı:\n")

for source, count in counter.items():
    print(f"{source}: {count}")