from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
)

from services.market_service import MarketService

from ui.widgets.news_card import NewsCard
from ui.widgets.summary_card import SummaryCard
from ui.widgets.market_card import MarketCard
from ui.widgets.trend_card import TrendCard
from ui.widgets.headline_card import HeadlineCard

from workers.news_worker import NewsWorker


class HomePage(QWidget):

    def __init__(self):
        super().__init__()

        self.market_service = MarketService()
        self.thread = None
        self.worker = None

        self.setup_ui()
        self.load_dashboard()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(20)

        # Başlık
        header_layout = QHBoxLayout()
        logo = QLabel("🌍")
        logo.setObjectName("logo")

        title_layout = QVBoxLayout()
        title = QLabel("NewsPilot AI")
        title.setObjectName("title")
        subtitle = QLabel("AI Destekli Global Gündem Paneli")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addWidget(logo)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # Manşet kartı
        self.headline_card = HeadlineCard()
        self.main_layout.addWidget(self.headline_card)

        # İçerik (haberler + sağ panel)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        self.news_layout = QVBoxLayout()
        self.news_layout.setSpacing(15)

        news_container = QWidget()
        news_container.setLayout(self.news_layout)

        self.news_scroll = QScrollArea()
        self.news_scroll.setWidgetResizable(True)
        self.news_scroll.setWidget(news_container)
        self.news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        self.trend_card = TrendCard()
        self.market_card = MarketCard(
            markets=self.market_service.get_market_data()
        )

        right_layout.addWidget(self.trend_card)
        right_layout.addWidget(self.market_card)
        right_layout.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        content_layout.addWidget(self.news_scroll, 3)
        content_layout.addWidget(right_widget, 1)
        self.main_layout.addLayout(content_layout)

        # Özet kartı
        self.summary_card = SummaryCard()
        self.main_layout.addWidget(self.summary_card)

        # Yükleniyor etiketi
        self.loading_label = QLabel("⏳ Haberler yükleniyor...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setObjectName("loadingLabel")
        self.main_layout.addWidget(self.loading_label)

    def load_dashboard(self):
        if self.thread is not None and self.thread.isRunning():
            return

        self.loading_label.show()

        # Eski kartları temizle
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.thread = QThread(self)
        self.worker = NewsWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_dashboard_data)
        self.worker.error.connect(self.handle_dashboard_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def handle_dashboard_data(self, result):
        self.loading_label.hide()

        articles = result.get("articles", [])
        analysis = result.get("analysis", {})

        self.headline_card.set_data(analysis.get("headline", ""))

        for article in articles:
            card = NewsCard(
                title=article.get("title", ""),
                source=article.get("source", ""),
                time=article.get("published_at", ""),
                description=article.get("description", ""),
                category="Global",
                url=article.get("url", ""),
            )
            self.news_layout.addWidget(card)

        self.news_layout.addStretch()

        self.summary_card.set_summary(analysis.get("summary", ""))
        self.trend_card.set_trends(analysis.get("trends", []))

        self.thread = None
        self.worker = None

    def handle_dashboard_error(self, message):
        self.loading_label.hide()
        self.thread = None
        self.worker = None

        QMessageBox.critical(self, "Hata", message)