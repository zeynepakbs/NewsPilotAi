# ui/news_page.py
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)

from workers.news_worker import NewsWorker


class NewsPage(QWidget):

    def __init__(self, back_callback):
        super().__init__()

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
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(12)

        self.back_button = QPushButton("← Geri")
        self.back_button.clicked.connect(self.back_callback)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setFixedHeight(28)
        main_layout.addWidget(self.back_button)

        self.title = QLabel("Gündem Haberleri")
        title_font = self.title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        self.title.setFont(title_font)
        main_layout.addWidget(self.title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame)

        self.container = QWidget()
        self.news_layout = QVBoxLayout(self.container)
        self.news_layout.setContentsMargins(0, 0, 0, 0)
        self.news_layout.setSpacing(12)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

    def load_news(self):
        self.thread = QThread(self)
        self.worker = NewsWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.show_news)
        self.worker.error.connect(self.show_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_thread_finished)

        self.thread.start()

    def on_thread_finished(self):
        self.worker = None
        self.thread = None

    def show_news(self, result):
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        agenda = result.get("agenda", [])
        if not agenda:
            empty = QLabel("Haber bulunamadı.")
            empty.setWordWrap(True)
            self.news_layout.addWidget(empty)
        else:
            for item in agenda:
                title_label = QLabel(item.get("title", "Başlık yok"))
                font = title_label.font()
                font.setBold(True)
                title_label.setFont(font)
                title_label.setWordWrap(True)

                summary_label = QLabel(item.get("summary", ""))
                summary_label.setWordWrap(True)

                self.news_layout.addWidget(title_label)
                self.news_layout.addWidget(summary_label)

        self.news_layout.addStretch()

    def show_error(self, message):
        label = QLabel(f"Hata: {message}")
        label.setWordWrap(True)
        self.news_layout.addWidget(label)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(3000)
        self.thread = None
        self.worker = None
        event.accept()