from services.news.models.article import Article
from services.news.ranking.headline_cluster import HeadlineCluster


class DuplicateDetector:

    STOP_WORDS = {
        "ve",
        "ile",
        "bir",
        "bu",
        "su",
        "son",
        "yeni",
        "icin",
        "hakkinda",
        "olarak",
        "acikladi",
        "bildirdi",
        "duyurdu",
        "the",
        "a",
        "an",
        "new",
        "of",
        "to",
        "in",
        "on"
    }


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



    def _tokenize(self, text: str):

        text = self._normalize(text)

        words = text.split()

        result = set()


        for word in words:

            if word in self.STOP_WORDS:
                continue


            if len(word) < 3:
                continue


            suffixes = [
                "lari",
                "leri",
                "lar",
                "ler",
                "nin",
                "dan",
                "den",
                "dir",
                "tir",
                "ini",
                "unu",
                "ile"
            ]


            for suffix in suffixes:

                if (
                    word.endswith(suffix)
                    and len(word) > len(suffix) + 3
                ):

                    word = word[:-len(suffix)]
                    break


            result.add(word)


        return result



    def _similarity(
        self,
        title1: str,
        title2: str
    ):

        words1 = self._tokenize(title1)
        words2 = self._tokenize(title2)


        if not words1 or not words2:
            return 0


        common = words1.intersection(words2)


        smaller = min(
            len(words1),
            len(words2)
        )


        return len(common) / smaller



    def _choose_title(
        self,
        articles: list[Article]
    ):

        return max(
            articles,
            key=lambda article: (
                article.priority,
                len(article.title)
            )
        ).title



    def remove_duplicates(
        self,
        articles: list[Article],
        threshold: float = 0.45
    ):

        groups = []


        for article in articles:

            added = False


            for group in groups:


                first_article = group[0]


                # farklı diller aynı cluster olmasın
                if article.lang != first_article.lang:
                    continue



                similarity = self._similarity(
                    article.title,
                    first_article.title
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


            cluster = HeadlineCluster(

                title=self._choose_title(group),

                articles=group,

                score=0

            )


            clusters.append(cluster)



        return clusters