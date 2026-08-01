from services.news.news_service import NewsService
from services.news.ranking.duplicate_detector import DuplicateDetector

news_service = NewsService()
articles = news_service.get_combined_news()

detector = DuplicateDetector()

# 1) Daha geniş aralıkta sayıları gör
detector.diagnose_threshold(articles)

# 2) 0.45 gibi düşük bir değerde kümelerin İÇİNİ gör
detector.inspect_clusters(articles, threshold=0.50, min_size=3)