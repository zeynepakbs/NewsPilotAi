from services.news.news_service import NewsService
from services.news.ranking.duplicate_detector import DuplicateDetector

service = NewsService()

articles = service.get_turkey_news()

detector = DuplicateDetector()

groups = detector.group(articles)

print(f"Toplam haber: {len(articles)}")
print(f"Grup sayısı : {len(groups)}")

for group in groups[:10]:
    print("\n----------------")
    print(f"{len(group)} kaynak")

    for article in group:
        print(f"{article.source}: {article.title}")