from PySide6.QtCore import QObject, Signal

from services.news.news_service import NewsService
from services.news.ai.ai_service import AIService

from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.importance_calculator import ImportanceCalculator

from services.news.agenda.agenda_selector import AgendaSelector
from services.news.sumarizer.plain_summary import build_plain_summary


class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)


    def __init__(self):
        super().__init__()

        self.news_service = NewsService()
        self.ai_service = AIService()

        self.duplicate_detector = DuplicateDetector()
        self.category_classifier = CategoryClassifier()
        self.importance_calculator = ImportanceCalculator()

        self.agenda_selector = AgendaSelector(
            max_per_region=2
        )


    def _build_tier_lists(self, scored_clusters):
        """
        Önem puanına göre (AI'ya sormadan) kritik / az kritik
        haber listelerini oluşturur. Metin, çevrilmiş description'dan
        üretilir; ekstra Gemini isteği yapılmaz.
        """

        kritik = []
        az_kritik = []

        for cluster in scored_clusters:

            tier = ImportanceCalculator.tier_for(cluster.score)

            if tier is None:
                continue

            item = {

                "category": getattr(cluster, "category", "") or "",

                "region": self._resolve_region(cluster),

                "importance": cluster.score,

                "repeat_count": cluster.repeat_count,

                "sources": cluster.sources,

                "body": build_plain_summary(cluster),

            }

            if tier == "kritik":
                kritik.append(item)
            else:
                az_kritik.append(item)

        return kritik, az_kritik


    def _resolve_region(self, cluster):

        from collections import Counter

        regions = [
            article.region
            for article in cluster.articles
            if getattr(article, "region", "")
        ]

        if not regions:
            return ""

        return Counter(regions).most_common(1)[0][0]


    def run(self):

        try:

            # 1) Haberleri çek
            articles = self.news_service.get_combined_news()


            # 2) Çeviri
            articles = self.ai_service.translate_articles(
                articles
            )


            # 3) Benzer haberleri grupla (Article -> HeadlineCluster)
            clusters = self.duplicate_detector.remove_duplicates(
                articles
            )


            # 4) Kategorileri belirle (cluster.category)
            clusters = self.category_classifier.classify(
                clusters
            )


            # 5) AI analiz (cluster.importance_score, is_newsworthy, summary)
            #    -- yalnızca en üstteki N cluster için, kota koruması var
            analyzed_clusters = self.ai_service.analyze_clusters(
                clusters
            )


            # 6) Önem puanı hesapla (senin formülüne göre, AI gerektirmez)
            scored_clusters = self.importance_calculator.calculate(
                analyzed_clusters
            )


            # 7) Kritik gündemi seç (bölge bazlı, home page için)
            agenda = self.agenda_selector.select(
                scored_clusters
            )


            # 8) Kritik / az kritik listeleri (AI'sız, description'dan)
            kritik, az_kritik = self._build_tier_lists(
                scored_clusters
            )


            # 9) UI'a gönder
            self.finished.emit(
                {
                    "agenda": agenda,
                    "kritik": kritik,
                    "az_kritik": az_kritik,
                }
            )


        except Exception as e:

            self.error.emit(
                str(e)
            )