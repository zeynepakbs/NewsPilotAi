import re
import unicodedata

from services.news.models.article import Article


class Normalizer:


    REMOVE_WORDS = [
        "son dakika",
        "son dakika:",
        "video",
        "foto galeri",
        "canlı",
    ]



    def normalize(
        self,
        articles: list[Article]
    ) -> list[Article]:


        normalized = []


        for article in articles:


            title = article.title.lower()


            title = unicodedata.normalize(
                "NFKD",
                title
            )

            title = title.encode(
                "ascii",
                "ignore"
            ).decode(
                "utf-8"
            )


            for word in self.REMOVE_WORDS:

                title = title.replace(
                    word,
                    ""
                )


            title = re.sub(
                r"[^\w\s]",
                " ",
                title
            )


            title = re.sub(
                r"\s+",
                " ",
                title
            )


            article.title = title.strip()


            if article.description:

                article.description = article.description.strip()


            normalized.append(article)



        return normalized