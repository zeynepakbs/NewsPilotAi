from services.news.ai.translator import Translator
from services.news.ai.news_ranker import NewsRanker
from services.news.ai.news_analyzer import NewsAnalyzer


class AIService:


    def __init__(self):

        self.translator = Translator()

        self.ranker = NewsRanker()

        self.analyzer = NewsAnalyzer()



    # ÇEVİRİ

    def translate_articles(self, articles):

        return self.translator.translate_articles(
            articles
        )



    # GÜNDEM SIRALAMA

    def rank_news(self, articles):

        return self.ranker.rank_news(
            articles
        )



    # TEK HABER KÜMESİ ANALİZİ

    def analyze_cluster(self, cluster):

        return self.analyzer.analyze(
            cluster
        )



    # TÜM KÜMELERİ ANALİZ ET

    def analyze_clusters(self, clusters):

        return self.analyzer.analyze_all(
            clusters
        )



    # PIPELINE ANA ANALİZ METODU

    def analyze(self, clusters):

        return self.analyzer.analyze_all(
            clusters
        )