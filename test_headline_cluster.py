from services.news.news_service import NewsService
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.importance_calculator import ImportanceCalculator
from services.news.ranking.headline_cluster import HeadlineClusterBuilder

service = NewsService()

# Tüm bölgelerden haberleri topla
articles = []

for country in ["tr", "us", "eu"]:
    try:
        news = service.get_news(country)
        print(f"{country.upper()} -> {len(news)} haber")
        articles.extend(news)
    except Exception as e:
        print(f"{country.upper()} hata: {e}")

print(f"\nToplam haber: {len(articles)}\n")

# Kategori belirle
classifier = CategoryClassifier()

for article in articles:
    article.category = classifier.classify(article).value

# Aynı haberleri grupla
groups = DuplicateDetector().group(articles)

# Önem puanı hesapla
ranked = ImportanceCalculator().calculate(groups)

# Gündem kümelerini oluştur
clusters = HeadlineClusterBuilder().build(ranked)

print(f"Toplam Gündem: {len(clusters)}\n")

for cluster in clusters[:20]:

    print("=" * 80)
    print(f"Başlık   : {cluster.title}")
    print(f"Kategori : {cluster.category}")
    print(f"Skor     : {cluster.score}")
    print(f"Kaynak   : {cluster.source_count}")

    for article in cluster.articles:
        print(f"  - [{article.source}]")