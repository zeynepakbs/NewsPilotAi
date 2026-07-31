from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QFrame,
)

from workers.news_worker import NewsWorker


# NewsService.get_combined_news() içinde collector anahtarları
# ("tr", "us", "eu", "as") kaynak bölge kodu olarak kullanılıyor.
# Ancak UI burada artık insan okunabilir İngilizce bölge adlarına sahip.
REGION_LABELS = [
    ("Turkey", "🇹🇷 TURKEY"),
    ("USA", "🇺🇸 USA"),
    ("Europe", "🇪🇺 EUROPE"),
    ("Asia", "🌏 ASIA"),
    ("Middle East", "🌍 MIDDLE EAST"),
    ("Global", "🌐 GLOBAL"),
]


def _get(item, key, default=""):
    """Hem dict hem de Article gibi obje tipleriyle çalışır."""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


class HomePage(QWidget):

    def __init__(self):
        super().__init__()

        self.thread = None
        self.worker = None

        self.setup_ui()
        self.load_dashboard()


    def setup_ui(self):

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            40, 30, 40, 30
        )

        self.main_layout.setSpacing(10)


        header_row = QHBoxLayout()

        title = QLabel(
            "Günlük Gündem Özeti"
        )

        font = QFont()
        font.setPointSize(16)
        font.setBold(True)

        title.setFont(font)

        header_row.addWidget(title)

        header_row.addStretch()

        self.main_layout.addLayout(header_row)


        self.news_layout = QVBoxLayout()
        self.news_layout.setSpacing(6)


        container = QWidget()
        container.setLayout(
            self.news_layout
        )


        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setWidget(
            container
        )


        self.main_layout.addWidget(
            self.scroll
        )


        self.loading_label = QLabel(
            "Haberler yükleniyor..."
        )

        self.loading_label.setAlignment(
            Qt.AlignCenter
        )

        self.main_layout.addWidget(
            self.loading_label
        )


    def load_dashboard(self):

        if self.thread and self.thread.isRunning():
            return


        self._clear_news_layout()


        self.thread = QThread(self)

        self.worker = NewsWorker()

        self.worker.moveToThread(
            self.thread
        )


        self.thread.started.connect(
            self.worker.run
        )

        self.worker.finished.connect(
            self.handle_dashboard_data
        )

        self.worker.error.connect(
            self.handle_dashboard_error
        )


        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )


        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.error.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )


        self.thread.start()



    def _clear_news_layout(self):

        while self.news_layout.count():

            item = self.news_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()



    def _add_region_section(
        self,
        title,
        items
    ):


        region = QLabel(title)

        font = QFont()
        font.setPointSize(13)
        font.setBold(True)

        region.setFont(font)

        self.news_layout.addWidget(
            region
        )


        if not items:

            empty = QLabel(
                "Kritik gündem bulunamadı."
            )

            self.news_layout.addWidget(
                empty
            )


        else:

            for index, item in enumerate(items[:2], 1):

                headline = QLabel(
                    f"{index}. {_get(item, 'title', '')}"
                )

                headline_font = QFont()
                headline_font.setBold(True)

                headline.setFont(
                    headline_font
                )

                headline.setWordWrap(True)


                summary = QLabel(
                    _get(item, "summary", "")
                )

                summary.setWordWrap(True)


                self.news_layout.addWidget(
                    headline
                )

                self.news_layout.addWidget(
                    summary
                )


        self.news_layout.addSpacing(
            15
        )



    def handle_dashboard_data(
        self,
        result
    ):

        self.loading_label.hide()

        self._clear_news_layout()


        # agenda listesi geliyor
        agenda = result.get(
            "agenda",
            []
        )


        for region_key, label in REGION_LABELS:

            items = [
                x for x in agenda
                if _get(x, "region") == region_key
            ]


            self._add_region_section(
                label,
                items
            )


        self.news_layout.addStretch()


        self.thread = None
        self.worker = None



    def handle_dashboard_error(
        self,
        message
    ):

        self.loading_label.hide()

        QMessageBox.critical(
            self,
            "Hata",
            message
        )


    def stop_worker(self):

        if (
            self.thread
            and self.thread.isRunning()
        ):

            self.thread.quit()
            self.thread.wait(3000)


    def closeEvent(self, event):

        self.stop_worker()

        super().closeEvent(event)