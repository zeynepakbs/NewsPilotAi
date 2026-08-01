from PySide6.QtCore import QObject, Signal, Slot

from services.news.news_service import NewsService
from services.news.ai.gemini_service import GeminiService

from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.importance_calculator import ImportanceCalculator

from services.news.agenda.agenda_selector import AgendaSelector
from services.news.script.script_service import ScriptService
from services.news.sumarizer.plain_summary import build_plain_summary
from services.news.voice.tts_service import TTSService



class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, country=None):
        super().__init__()

        self.country = country

        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        self.duplicate_detector = DuplicateDetector()
        self.category_classifier = CategoryClassifier()
        self.importance_calculator = ImportanceCalculator()
        self.script_service = ScriptService()
        self.tts_service = TTSService()
        self.agenda_selector = AgendaSelector(max_per_region=2)

    MAX_AI_ANALYSIS_PER_REGION = 3

    def _resolve_region(self, cluster):
        from collections import Counter

        regions = [
            article.region
            for article in cluster.articles
            if getattr(
                article,
                "region",
                ""
            )
        ]

        if not regions:
            return ""

        return Counter(
            regions
        ).most_common(1)[0][0]

    def _build_tier_lists(self, scored_clusters):
        kritik = []

        for cluster in scored_clusters:
            tier = ImportanceCalculator.tier_for(
                cluster.score
            )

            if tier != "kritik":
                continue

            item = {
                "category": getattr(
                    cluster,
                    "category",
                    ""
                ) or "",

                "region": self._resolve_region(
                    cluster
                ),

                "importance": cluster.score,

                "repeat_count": cluster.repeat_count,

                "sources": cluster.sources,

                "body": build_plain_summary(
                    cluster
                ),
            }

            kritik.append(
                item
            )

        return kritik

    @Slot()
    def run(self):
        try:
            print(
                "[NewsWorker] başladı"
            )

            # 1 - Haberleri çek
            articles = (
                self.news_service
                .get_combined_news()
            )

            print(
                f"[NewsWorker] {len(articles)} haber geldi"
            )

            # 2 - Çeviri
            articles = (
                self.gemini_service
                .translate_articles(
                    articles
                )
            )

            print(
                "[NewsWorker] çeviri tamam"
            )

            # 3 - Bölgelere ayır
            articles_by_region = {}

            for article in articles:
                region = getattr(
                    article,
                    "region",
                    ""
                ) or ""

                articles_by_region.setdefault(
                    region,
                    []
                ).append(
                    article
                )

            scored_clusters = []

            # 4 - Bölge bazlı analiz
            for region, region_articles in articles_by_region.items():
                try:
                    print(
                        f"[NewsWorker] {region} analiz ediliyor"
                    )

                    clusters = (
                        self.duplicate_detector
                        .remove_duplicates(
                            region_articles
                        )
                    )

                    clusters = (
                        self.category_classifier
                        .classify(
                            clusters
                        )
                    )

                    analyzed_clusters = (
                        self.gemini_service
                        .analyzer
                        .analyze_all(
                            clusters,
                            max_ai_analysis=
                            self.MAX_AI_ANALYSIS_PER_REGION
                        )
                    )

                    region_scored = (
                        self.importance_calculator
                        .calculate(
                            analyzed_clusters
                        )
                    )

                    scored_clusters.extend(
                        region_scored
                    )

                except Exception as e:
                    print(
                        f"[NewsWorker] {region} hata:",
                        e
                    )

            # 5 - Gündem seçimi
            agenda = (
                self.agenda_selector
                .select(
                    scored_clusters
                )
            )

            # 6 - Kritik haberler
            kritik = (
                self._build_tier_lists(
                    scored_clusters
                )
            )

            # 7 - Haber senaryosu oluştur
            print(
                "[NewsWorker] Script oluşturuluyor"
            )

            def agenda_score(cluster):
                return (
                    cluster.repeat_count * 3
                    +
                    len(cluster.sources) * 2
                    +
                    cluster.score
                )

            top_clusters = sorted(
                scored_clusters,
                key=agenda_score,
                reverse=True
            )[:10]

            print("\n[TOP GÜNDEM]")
            for cluster in top_clusters:
                print(
                    "Tekrar:",
                    cluster.repeat_count,
                    "| Kaynak:",
                    len(cluster.sources),
                    "| Skor:",
                    round(cluster.score, 2),
                    "|",
                    getattr(
                        cluster,
                        "headline",
                        getattr(cluster, "title", "")
                    )
                )

            script_news = []

            for cluster in top_clusters:
                script_news.append(
                    {
                        "title": getattr(
                            cluster,
                            "headline",
                            getattr(cluster, "title", "")
                        ),

                        "summary": build_plain_summary(
                            cluster
                        ),

                        "importance": agenda_score(cluster)
                    }
                )

            script = self.script_service.generate(
                script_news
            )

            print(
                "[NewsWorker] Script tamamlandı"
            )

            # 8 - TTS
            print("[NewsWorker] TTS başlıyor")

            audio_path = None
            try:
                audio_path = self.tts_service.generate(
                    script,
                    filename="headless_white_collar.mp3"
                )

                print(
                    "[NewsWorker] Audio:",
                    audio_path
                )

            except Exception as e:
                print(
                    "[NewsWorker] TTS HATA:",
                    e
                )

            result = {
                "agenda": agenda,
                "kritik": kritik,
                "script": script,
                "audio": audio_path,
            }

            print(
                "[NewsWorker] tamamlandı"
            )

            self.finished.emit(
                result
            )

        except Exception as e:
            print(
                "[NewsWorker ERROR]",
                e
            )

            self.error.emit(
                str(e)
            )