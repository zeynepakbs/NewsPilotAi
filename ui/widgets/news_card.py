import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)


class NewsCard(QFrame):

    clicked = Signal()

    def __init__(
        self,
        title: str,
        source: str,
        time: str,
        description: str,
        category: str = "Genel",
        url: str = ""
    ):
        super().__init__()

        self.url = url

        self.setObjectName("newsCard")
        self.setCursor(Qt.PointingHandCursor)

        self.setup_ui(
            title,
            source,
            time,
            description,
            category
        )

    def setup_ui(
        self,
        title,
        source,
        time,
        description,
        category
    ):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ==========================
        # Üst Bilgi
        # ==========================

        top_layout = QHBoxLayout()

        source_label = QLabel(f"📰 {source}")
        source_label.setObjectName("newsSource")

        time_label = QLabel(time)
        time_label.setObjectName("newsTime")

        top_layout.addWidget(source_label)
        top_layout.addStretch()
        top_layout.addWidget(time_label)

        # ==========================
        # Başlık
        # ==========================

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setObjectName("newsTitle")

        # ==========================
        # Açıklama
        # ==========================

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setObjectName("newsDescription")

        # ==========================
        # Alt Kısım
        # ==========================

        bottom_layout = QHBoxLayout()

        category_label = QLabel(f"🌍 {category}")
        category_label.setObjectName("newsCategory")

        detail_button = QPushButton("🔗 Haberi Oku")
        detail_button.setObjectName("detailButton")

        detail_button.clicked.connect(self.open_news)

        bottom_layout.addWidget(category_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(detail_button)

        layout.addLayout(top_layout)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addLayout(bottom_layout)

    def open_news(self):

        if self.url:
            webbrowser.open(self.url)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)