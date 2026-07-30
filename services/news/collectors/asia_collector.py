from typing import List

from services.news.ingestion.rss_provider import RSSProvider
from services.news.models.article import Article


class AsiaCollector:
    """
    Asya haberlerini toplar.
    """

    def __init__(self):
        self.provider = RSSProvider()

    def collect(self) -> List[Article]:
        return self.provider.fetch_country_news("asia")