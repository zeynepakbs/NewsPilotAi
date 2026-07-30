from typing import List

from services.news.models.article import Article
from services.news.ingestion.rss_provider import RSSProvider


class TurkeyCollector:
    """
    Türkiye haberlerini toplar.

    Görevi:
    - RSSProvider'ı çağırmak
    - Türkiye kaynaklarından haberleri almak
    - Article listesi döndürmek
    """

    def __init__(self):
        self.provider = RSSProvider()

    def collect(self) -> List[Article]:
        return self.provider.fetch_country_news("tr")