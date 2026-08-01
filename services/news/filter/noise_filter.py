class NewsNoiseFilter:


    BLOCKED_KEYWORDS = [
        "burç",
        "burcu",
        "astroloji",
        "fal",
        "günlük yorum",
        "tarot",
        "magazin",
        "ünlü",
        "dizi",
        "oyuncu",
    ]


    def filter(self, articles):

        cleaned = []

        removed = 0

        for article in articles:

            text = (
                article.title
                + " "
                + getattr(article, "description", "")
            ).lower()


            if any(
                keyword in text
                for keyword in self.BLOCKED_KEYWORDS
            ):
                removed += 1
                continue


            cleaned.append(article)


        print(
            f"[NoiseFilter] {removed} gereksiz haber elendi "
            f"({len(articles)} -> {len(cleaned)})"
        )


        return cleaned