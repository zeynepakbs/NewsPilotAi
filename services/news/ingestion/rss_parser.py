from typing import List

from services.news.models.article import Article


class RSSParser:

    def parse(
        self,
        feed,
        source_name: str,
        priority: int
    ) -> List[Article]:

        articles = []

        for entry in feed.entries:

            article = Article(
                title=getattr(entry, "title", ""),
                description=getattr(entry, "summary", ""),
                url=getattr(entry, "link", ""),
                source=source_name,
                priority=priority,
                published_at=None
            )

            articles.append(article)

        return articles