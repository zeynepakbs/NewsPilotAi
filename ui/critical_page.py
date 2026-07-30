from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)

from workers.news_worker import NewsWorker


class CriticalNewsPage(QWidget):

    RESULT_KEY = "kritik"
    PAGE_TITLE = "Kritik Haberler"


    def __init__(self, back_callback):
        super().__init__()

        self.back_callback = back_callback
        self.thread = None
        self.worker = None

        self.setup_ui()
        self.load_news()


    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.back_button = QPushButton("← Geri")
        self.back_button.clicked.connect(self.back_callback)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setFixedHeight(28)
        layout.addWidget(self.back_button)

        title = QLabel(self.PAGE_TITLE)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title.setFont(font)
        layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.items_layout = QVBoxLayout(self.container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(16)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.loading_label = QLabel("Yükleniyor...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)


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

        self.thread.start()


    def _clear_items(self):

        while self.items_layout.count():

            item = self.items_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()


    def show_news(self, result):

        self.loading_label.hide()

        self._clear_items()

        items = result.get(self.RESULT_KEY, [])

        if not items:

            empty = QLabel("Bu kategoride haber bulunamadı.")
            empty.setWordWrap(True)
            self.items_layout.addWidget(empty)

        else:

            for entry in items:

                body_label = QLabel(entry.get("body", ""))
                body_label.setWordWrap(True)
                body_label.setContentsMargins(0, 0, 0, 4)

                self.items_layout.addWidget(body_label)

                meta_text = self._build_meta_text(entry)

                if meta_text:

                    meta_label = QLabel(meta_text)
                    meta_label.setStyleSheet(
                        "color: #888888; font-size: 10px;"
                    )
                    meta_label.setContentsMargins(0, 0, 0, 14)

                    self.items_layout.addWidget(meta_label)

        self.items_layout.addStretch()


    def _build_meta_text(self, entry):

        parts = []

        category = entry.get("category")
        if category:
            parts.append(category)

        repeat_count = entry.get("repeat_count")
        if repeat_count:
            parts.append(f"{repeat_count} kaynak")

        return " · ".join(parts)


    def show_error(self, message):

        self.loading_label.hide()

        error = QLabel(f"Hata: {message}")
        error.setWordWrap(True)
        self.items_layout.addWidget(error)


    def closeEvent(self, event):

        try:
            if self.thread and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait(3000)
        except RuntimeError:
            pass

        self.thread = None
        self.worker = None
        event.accept()