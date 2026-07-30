from services.news.collectors.turkey_collector import TurkeyCollector
from services.news.collectors.us_collector import USCollector
from services.news.collectors.europe_collector import EuropeCollector
from services.news.collectors.asia_collector import AsiaCollector


from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.importance_calculator import ImportanceCalculator


from services.news.ai.ai_service import AIService


from services.news.agenda.agenda_selector import AgendaSelector



class NewsPipeline:


    def __init__(self):

        self.collectors = {

            "turkiye": TurkeyCollector(),

            "amerika": USCollector(),

            "avrupa": EuropeCollector(),

            "asya": AsiaCollector()

        }


        self.duplicate_detector = DuplicateDetector()

        self.category_classifier = CategoryClassifier()

        self.importance_calculator = ImportanceCalculator()

        self.ai_service = AIService()

        self.agenda_selector = AgendaSelector()



    def run(self):

        result = {}



        for region, collector in self.collectors.items():

            print(
                f"\n[{region}] başlıyor..."
            )



            try:


                # 1 - Haberleri topla

                articles = collector.collect()


                print(
                    "Toplanan haber:",
                    len(articles)
                )



                # 2 - Benzer haberleri grupla

                clusters = self.duplicate_detector.remove_duplicates(
                    articles
                )


                print(
                    "Küme sayısı:",
                    len(clusters)
                )



                # 3 - Kategori belirle

                clusters = self.category_classifier.classify(
                    clusters
                )



                # 4 - İlk matematiksel önem skoru

                clusters = self.importance_calculator.calculate(
                    clusters
                )



                # 5 - AI için aday havuzu oluştur

                clusters.sort(

                    key=lambda x: x.score,

                    reverse=True

                )


                candidate_clusters = clusters[:30]


                print(
                    f"{region}: AI analiz adayı {len(candidate_clusters)}"
                )



                # 6 - Gemini analiz

                analyzed = self.ai_service.analyze_clusters(
                    candidate_clusters
                )



                # 7 - AI sonuçlarını cluster içine işle

                final_clusters = []



                for index, item in enumerate(analyzed):


                    cluster = candidate_clusters[index]


                    analysis = item.get(
                        "analysis",
                        {}
                    )



                    cluster.summary = analysis.get(
                        "summary",
                        ""
                    )



                    cluster.keywords = analysis.get(
                        "keywords",
                        []
                    )



                    cluster.importance_reason = analysis.get(
                        "importance_reason",
                        ""
                    )



                    cluster.is_newsworthy = analysis.get(
                        "is_newsworthy",
                        True
                    )



                    cluster.importance_score = analysis.get(
                        "importance_score",
                        cluster.score
                    )



                    ai_category = analysis.get(
                        "category"
                    )



                    if ai_category:

                        cluster.category = ai_category



                    if cluster.is_newsworthy:

                        final_clusters.append(
                            cluster
                        )




                # 8 - AI skoruna göre tekrar sırala

                final_clusters.sort(

                    key=lambda x: x.importance_score,

                    reverse=True

                )



                # İlk 10 gündem

                top_clusters = final_clusters[:10]



                print(
                    f"{region}: {len(top_clusters)} haber seçildi"
                )



                for item in top_clusters[:3]:

                    print(

                        item.title,

                        "score:",

                        item.importance_score

                    )




                # 9 - Son çıktı

                agenda = self.agenda_selector.select(
                    top_clusters
                )



                result[region] = agenda




            except Exception as e:


                print(

                    f"{region} hata:",

                    e

                )


                result[region] = []




        return result