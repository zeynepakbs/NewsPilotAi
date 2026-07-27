from services.news_service import NewsService
from services.ai_service import GeminiService


class SummaryService:

    def __init__(self):
        self.news_service = NewsService()
        self.ai_service = GeminiService()

    def summarize_country(self, country):

        articles = self.news_service.get_news(country)

        if not articles:
            return "Haber bulunamadı."

        headlines = "\n".join(
            f"- {article['title']}" for article in articles
        )

        prompt = f"""
Aşağıdaki haber başlıklarını analiz et.

{headlines}

Kurallar:

- Türkçe cevap ver.
- En önemli gelişmeleri maddeler halinde yaz.
- Gereksiz detay verme.
- Tarafsız ol.
- Maksimum 250 kelime kullan.
"""

        return self.ai_service.ask(prompt)