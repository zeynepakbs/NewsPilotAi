from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)

from PySide6.QtCore import (
    Qt,
    QThread,
)

from services.news.news_worker import NewsWorker


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

        self.setStyleSheet(
            """
            QWidget {
                background: white;
                color: black;
            }

            QLabel {
                color: black;
            }

            QPushButton {
                background: white;
                color: black;
                border: none;
            }

            QPushButton:hover {
                text-decoration: underline;
            }

            QScrollArea {
                background: white;
            }
            """
        )


        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        main_layout.setSpacing(
            12
        )


        self.back_button = QPushButton(
            "← Geri"
        )

        self.back_button.clicked.connect(
            self.back_callback
        )

        self.back_button.setCursor(
            Qt.PointingHandCursor
        )

        self.back_button.setFixedHeight(
            28
        )

        main_layout.addWidget(
            self.back_button
        )


        self.title = QLabel(
            "Gündem Haberleri"
        )

        title_font = self.title.font()
        title_font.setBold(True)
        title_font.setPointSize(
            title_font.pointSize() + 2
        )

        self.title.setFont(
            title_font
        )

        main_layout.addWidget(
            self.title
        )


        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll.setFrameShape(
            QScrollArea.NoFrame
        )


        self.container = QWidget()


        self.news_layout = QVBoxLayout(
            self.container
        )

        self.news_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.news_layout.setSpacing(
            12
        )


        self.scroll.setWidget(
            self.container
        )


        main_layout.addWidget(
            self.scroll
        )



    def load_news(self):

        self.thread = QThread(
            self
        )

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


        # işlem bitince thread kapanır

        self.worker.finished.connect(
            self.thread.quit
        )


        self.worker.error.connect(
            self.thread.quit
        )


        # worker temizliği

        self.worker.finished.connect(
            self.worker.deleteLater
        )


        self.worker.error.connect(
            self.worker.deleteLater
        )


        # thread temizliği

        self.thread.finished.connect(
            self.thread.deleteLater
        )


        self.thread.finished.connect(
            self.on_thread_finished
        )


        self.thread.start()



    def on_thread_finished(self):

        self.worker = None
        self.thread = None




    NON_POLITICAL_KEYWORDS = [

        "stoper",
        "kaleci",
        "forvet",
        "transfer",
        "teknik direktör",
        "maç sonucu",
        "derbi",
        "şampiyonluk",
        "lig",
        "taraftar",

        "magazin",
        "boşandı",
        "evlendi",
        "nişanlandı",
        "ünlü çift",

    ]



    def _looks_non_political(self, item):

        text = (

            item.get(
                "baslik",
                ""
            )

            +

            " "

            +

            item.get(
                "ozet",
                ""
            )

        ).lower()


        return any(
            keyword in text
            for keyword in self.NON_POLITICAL_KEYWORDS
        )



    def create_news_item(self, item):

        title_label = QLabel(
            item.get(
                "baslik",
                "Başlık yok"
            )
        )


        title_font = title_label.font()

        title_font.setBold(
            True
        )

        title_label.setFont(
            title_font
        )

        title_label.setWordWrap(
            True
        )


        summary_label = QLabel(
            item.get(
                "ozet",
                ""
            )
        )


        summary_label.setWordWrap(
            True
        )


        self.news_layout.addWidget(
            title_label
        )


        self.news_layout.addWidget(
            summary_label
        )



        reason = item.get(
            "neden_onemli"
        )


        if reason:

            reason_label = QLabel(
                reason
            )

            reason_label.setStyleSheet(
                "color:#888888;font-size:10px;"
            )

            reason_label.setWordWrap(
                True
            )

            self.news_layout.addWidget(
                reason_label
            )



    def create_section(
        self,
        section_title,
        items
    ):

        heading = QLabel(
            section_title
        )


        font = heading.font()

        font.setBold(
            True
        )

        heading.setFont(
            font
        )


        self.news_layout.addWidget(
            heading
        )



        important_items = [

            item

            for item in items

            if not item.get(
                "onem_yok",
                False
            )

            and not self._looks_non_political(
                item
            )

        ]



        if not important_items:

            empty = QLabel(
                "Bu bölge için gündem bulunamadı."
            )

            self.news_layout.addWidget(
                empty
            )

            return



        for item in important_items[:2]:

            self.create_news_item(
                item
            )



    def show_news(self, news_data):


        while self.news_layout.count():

            item = self.news_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()



        sections = [

            (
                "Türkiye",
                "turkiye"
            ),

            (
                "Amerika",
                "amerika"
            ),

            (
                "Avrupa",
                "avrupa"
            ),

        ]



        for title, key in sections:

            items = []


            if isinstance(
                news_data,
                dict
            ):

                items = news_data.get(
                    key,
                    []
                )


            self.create_section(
                title,
                items
            )



    def show_error(self, message):

        label = QLabel(
            f"Hata: {message}"
        )

        label.setWordWrap(
            True
        )

        self.news_layout.addWidget(
            label
        )



    def closeEvent(self, event):

        if self.thread:

            if self.thread.isRunning():

                self.thread.quit()

                self.thread.wait(
                    3000
                )


        self.thread = None
        self.worker = None


        event.accept()