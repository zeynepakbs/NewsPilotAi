from typing import List

import feedparser

from services.news.ingestion.sources import RSS_SOURCES
from services.news.ingestion.rss_parser import RSSParser
from services.news.ingestion.normalizer import Normalizer
from services.news.models.article import Article


class RSSProvider:

    def __init__(self):

        self.parser = RSSParser()
        self.normalizer = Normalizer()


    def fetch_country_news(
        self,
        country: str
    ) -> List[Article]:


        articles = []


        sources = [
            source
            for source in RSS_SOURCES
            if source["country"] == country
        ]


        for source in sources:


            try:

                feed = feedparser.parse(
                    source["url"]
                )


                parsed_articles = self.parser.parse(
                    feed=feed,
                    source_name=source["name"],
                    priority=source["priority"]
                )


                parsed_articles = self.normalizer.normalize(
                    parsed_articles
                )


                articles.extend(
                    parsed_articles
                )


            except Exception as e:

                print(
                    f"{source['name']} okunamadı: {e}"
                )


        return articles