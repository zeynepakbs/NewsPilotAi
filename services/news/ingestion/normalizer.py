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

            # Görüntülenecek başlık: sadece gürültü kelimelerini ve
            # fazla boşlukları temizliyoruz, büyük/küçük harf ve
            # noktalama korunuyor ki arayüzde düzgün görünsün.
            title = article.title

            lowered = title.lower()

            for word in self.REMOVE_WORDS:

                idx = lowered.find(word)

                while idx != -1:

                    title = title[:idx] + title[idx + len(word):]
                    lowered = lowered[:idx] + lowered[idx + len(word):]

                    idx = lowered.find(word)


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