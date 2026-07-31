from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.news.collectors.europe_collector import EuropeCollector
from services.news.collectors.turkey_collector import TurkeyCollector
from services.news.collectors.us_collector import USCollector
from services.news.collectors.asia_collector import AsiaCollector
from services.news.models.article import Article
from services.news.region_detector import RegionDetector


class NewsService:

    def __init__(self):
        self.collectors = {
            "tr": TurkeyCollector(),
            "us": USCollector(),
            "eu": EuropeCollector(),
            "as": AsiaCollector(),
        }
        self.region_detector = RegionDetector()

    def get_news(self, country: str) -> List[Article]:
        collector = self.collectors.get(country.lower())

        if collector is None:
            raise ValueError(f"Desteklenmeyen ülke: {country}")

        return collector.collect()

    def get_turkey_news(self):
        return self.get_news("tr")

    def get_us_news(self):
        return self.get_news("us")

    def get_europe_news(self):
        return self.get_news("eu")

    def get_asia_news(self):
        return self.get_news("as")

    def get_combined_news(self):

        articles = []

        def _collect(region, collector):

            try:

                news = collector.collect()

                for article in news:
                    article.region = self.region_detector.detect(region, article)
                    article.lang = "tr" if region == "tr" else "en"

                return news

            except Exception as e:

                print(f"[NewsService] {region} haberleri alınamadı: {e}")

                return []

        # 4 bölge birbirinden bağımsız I/O işlemi olduğu için
        # paralel çekiyoruz; toplam süre en yavaş bölgenin
        # süresine iner, hepsinin toplamına değil.
        with ThreadPoolExecutor(max_workers=len(self.collectors)) as executor:

            futures = {
                executor.submit(_collect, region, collector): region
                for region, collector in self.collectors.items()
            }

            for future in as_completed(futures):

                articles.extend(
                    future.result()
                )

        return articles