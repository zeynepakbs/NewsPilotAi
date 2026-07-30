from services.news.news_service import NewsService
from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.importance_calculator import ImportanceCalculator

service = NewsService()

articles = service.get_turkey_news()

detector = DuplicateDetector()
groups = detector.group(articles)

calculator = ImportanceCalculator()
ranked_news = calculator.calculate(groups)

print(f"Toplam haber grubu: {len(ranked_news)}\n")

for news in ranked_news[:10]:
    print("=" * 80)
    print(f"Skor: {news.score}")
    print(f"Kaynak Sayısı: {len(news.articles)}")
    print(f"Başlık: {news.main_article.title}")

    print("Kaynaklar:")
    for article in news.articles:
        print(f"  - {article.source} (priority={article.priority})")