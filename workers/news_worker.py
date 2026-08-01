from PySide6.QtCore import QObject, Signal, Slot

from services.news.ai.gemini_service import GeminiService
from services.news.news_service import NewsService
from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.headline_ranker import HeadlineRanker
from services.news.ranking.importance_calculator import ImportanceCalculator
from services.news.agenda.agenda_selector import AgendaSelector
from services.news.sumarizer.plain_summary import build_plain_summary



class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)



    def __init__(self):

        super().__init__()


        self.news_service = NewsService()
        self.gemini_service = GeminiService()

        self.duplicate_detector = DuplicateDetector()

        self.category_classifier = CategoryClassifier()

        self.headline_ranker = HeadlineRanker()

        self.importance_calculator = ImportanceCalculator()


        self.agenda_selector = AgendaSelector(
            max_per_region=2
        )



    def _build_tier_lists(
        self,
        scored_clusters
    ):

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




    def _resolve_region(
        self,
        cluster
    ):

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

            self.duplicate_detector.diagnose_threshold(articles)

            self.duplicate_detector.inspect_clusters(
            articles,
            threshold=0.55,
            min_size=3
)



            # 2 - Duplicate temizleme

            print(
                "[NewsWorker] duplicate başlıyor"
            )

           
            

        

            clusters = (

                self.duplicate_detector
                .remove_duplicates(
                    articles
                )

            )



            print(
                f"[NewsWorker] {len(clusters)} cluster oluştu"
            )



            # 3 - Başlık tekrar sıralaması

            print(
                "[NewsWorker] headline ranking başlıyor"
            )


            clusters = (

                self.headline_ranker
                .rank(
                    clusters
                )

            )


            print(
                "[NewsWorker] headline ranking tamamlandı"
            )



            # 4 - Kategori sınıflandırma

            clusters = (

                self.category_classifier
                .classify(
                    clusters
                )

            )


            print(
                "[NewsWorker] kategori tamamlandı"
            )



            # 5 - Algoritmik önem puanı

            scored_clusters = (

                self.importance_calculator
                .calculate(
                    clusters
                )

            )


            print(
                "[NewsWorker] önem hesaplandı"
            )

            top_clusters = scored_clusters[:20]

            top_clusters = self.gemini_service.translate_clusters(
               top_clusters
        )

            print("[NewsWorker] Top cluster çevirisi tamamlandı")

            ai_editor = self.gemini_service.edit_news(
            top_clusters
        )    

            print("[NewsWorker] Gemini edit tamamlandı")
           



            # 6 - Gündem seçimi

            agenda = (

                self.agenda_selector
                .select(
                    scored_clusters
                )

            )



            # 7 - Kritik haberler

            kritik = (

                self._build_tier_lists(
                    scored_clusters
                )

            )



            print(
                "[NewsWorker] tamamlandı"
            )



            # 8 - UI gönder

            self.finished.emit(

                {
                    "agenda": agenda,
                    "kritik": kritik,
                    "ai_editor": ai_editor,
                }

            )



        except Exception as e:


            print(
                "[NewsWorker ERROR]",
                e
            )


            self.error.emit(
                str(e)
            )