from dataclasses import replace

from services.news.ai.gemini_client import GeminiClient


class Translator:

    def __init__(self):
        self.client = GeminiClient()

    def translate_articles(self, articles):

        to_translate = [
            (i, a)
            for i, a in enumerate(articles)
            if a.lang != "tr"
        ]

        if not to_translate:
            return articles

        items = ""

        for idx, (i, article) in enumerate(to_translate):
            items += f"""
{idx})

Başlık:
{article.title}

Açıklama:
{article.description}

"""

        prompt = f"""
Sen profesyonel bir haber editörü ve çevirmensin.

Aşağıdaki haberlerin başlık ve açıklamalarını
doğal ve akıcı Türkçeye çevir.

Anlamı değiştirme.

SADECE JSON döndür.

[
  {{
    "index":0,
    "title":"",
    "description":""
  }}
]

Haberler:

{items}
"""

        try:
            response = self.client.ask(prompt)
            translations = self.client.parse_json(response)

        except Exception as e:
            print(
                "[translate_articles] Çeviri başarısız, "
                f"orijinal haberler döndürülüyor. Hata: {e}"
            )
            return articles

        result = list(articles)

        for item in translations:

            local_index = item["index"]
            original_index = to_translate[local_index][0]

            original_article = result[original_index]

            result[original_index] = replace(
                original_article,
                title=item["title"],
                description=item["description"],
            )

        return result