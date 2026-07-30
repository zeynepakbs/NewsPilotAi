from dataclasses import dataclass

from services.news.models.article import Article



@dataclass
class HeadlineCluster:


    title: str

    articles: list[Article]


    score: int = 0


    category: str | None = None


    is_newsworthy: bool = True


    importance_score: int = 0


    summary: str = ""



    @property
    def source_count(self):

        return len(
            {
                article.source
                for article in self.articles
                if article.source
            }
        )


    @property
    def repeat_count(self):

        return len(self.articles)


    @property
    def sources(self):

        return list(
            {
                article.source
                for article in self.articles
                if article.source
            }
        )