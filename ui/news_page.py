from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame
)

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QObject
)

from services.news_service import NewsService
from services.ai_service import GeminiService

import json



class NewsWorker(QObject):

    finished = Signal(list)
    error = Signal(str)


    def __init__(self, country):

        super().__init__()

        self.country = country

        self.news_service = NewsService()
        self.ai_service = GeminiService()



    def run(self):

        try:

            news_list = self.news_service.get_news(
                self.country
            )


            translated = self.ai_service.translate_news(
                news_list
            )


            clean_json = (
                translated
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )


            data = json.loads(
                clean_json
            )


            self.finished.emit(
                data
            )


        except Exception as e:

            self.error.emit(
                str(e)
            )






class NewsPage(QWidget):


    def __init__(self, country, back_callback):

        super().__init__()


        self.country = country
        self.back_callback = back_callback


        self.thread = None
        self.worker = None


        self.setup_ui()

        self.load_news()






    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )


        self.back_button = QPushButton(
            "← Geri"
        )


        self.back_button.clicked.connect(
            self.back_callback
        )


        main_layout.addWidget(
            self.back_button
        )



        self.title = QLabel(
            f"{self.country.upper()} Gündem Haberleri"
        )


        self.title.setAlignment(
            Qt.AlignCenter
        )


        main_layout.addWidget(
            self.title
        )



        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )



        self.container = QWidget()


        self.news_layout = QVBoxLayout(
            self.container
        )


        self.scroll.setWidget(
            self.container
        )


        main_layout.addWidget(
            self.scroll
        )







    def load_news(self):


        self.thread = QThread()


        self.worker = NewsWorker(
            self.country
        )


        self.worker.moveToThread(
            self.thread
        )


        self.thread.started.connect(
            self.worker.run
        )


        self.worker.finished.connect(
            self.show_news
        )


        self.worker.error.connect(
            self.show_error
        )


        self.worker.finished.connect(
            self.thread.quit
        )


        self.worker.error.connect(
            self.thread.quit
        )


        self.thread.finished.connect(
            self.worker.deleteLater
        )


        self.thread.finished.connect(
            self.thread_finished
        )


        self.thread.start()






    def thread_finished(self):

        self.thread = None
        self.worker = None







    def create_news_card(self, text):


        card = QFrame()


        card.setFrameShape(
            QFrame.StyledPanel
        )


        card.setMinimumHeight(
            120
        )


        layout = QVBoxLayout(
            card
        )


        label = QLabel()


        label.setText(
            text
        )


        label.setWordWrap(
            True
        )


        layout.addWidget(
            label
        )


        self.news_layout.addWidget(
            card
        )







    def show_news(self, news_list):


        for news in news_list:


            if isinstance(news, dict):


                title = news.get(
                    "title",
                    "Başlık yok"
                )


                description = news.get(
                    "description",
                    ""
                )


                source = news.get(
                    "source",
                    "Bilinmiyor"
                )



                text = f"""
📰 {title}


{description}


Kaynak: {source}
"""



            else:


                text = str(news)



            self.create_news_card(
                text
            )








    def show_error(self, message):


        error = QLabel(
            f"Hata: {message}"
        )


        error.setWordWrap(
            True
        )


        self.news_layout.addWidget(
            error
        )







    def closeEvent(self, event):


        try:


            if self.thread:


                if self.thread.isRunning():


                    self.thread.quit()

                    self.thread.wait(3000)



        except RuntimeError:

            pass



        self.thread = None
        self.worker = None


        event.accept()