from services.news.models.article import Article
from services.news.ranking.headline_cluster import HeadlineCluster


class DuplicateDetector:


    def _normalize(self, text: str):

        text = text.lower()

        replacements = {
            "ı": "i",
            "ğ": "g",
            "ü": "u",
            "ş": "s",
            "ö": "o",
            "ç": "c"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text



    def _similarity(
        self,
        title1: str,
        title2: str
    ):

        title1 = self._normalize(title1)
        title2 = self._normalize(title2)


        words1 = set(title1.split())
        words2 = set(title2.split())


        if not words1 or not words2:
            return 0


        common = words1 & words2
        union = words1 | words2


        return len(common) / len(union)



    def remove_duplicates(
        self,
        articles: list[Article],
        threshold: float = 0.35
    ):

        groups = []


        for article in articles:

            added = False


            for group in groups:

                similarity = self._similarity(
                    article.title,
                    group[0].title
                )


                if similarity >= threshold:

                    group.append(article)
                    added = True
                    break



            if not added:

                groups.append(
                    [article]
                )



        clusters = []


        for group in groups:

            # En uzun başlığı temsilci olarak seç
            title = max(
                group,
                key=lambda x: len(x.title)
            ).title


            cluster = HeadlineCluster(

                title=title,

                articles=group,

                score=0

            )


            clusters.append(
                cluster
            )


        return clusters