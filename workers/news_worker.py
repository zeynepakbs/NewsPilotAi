from PySide6.QtCore import QObject, Signal

from services.news_service import NewsService
from services.ai_service import GeminiService


class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)

    def run(self):

        try:

            news_service = NewsService()
            ai_service = GeminiService()

            articles = news_service.get_combined_news()

            # Global (İngilizce) haberleri Türkçeye çevir,
            # Türkiye haberlerine dokunma
            articles = ai_service.translate_articles(articles)

            analysis = ai_service.analyze_news(articles)

            result = {
                "articles": articles,
                "analysis": analysis
            }

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))