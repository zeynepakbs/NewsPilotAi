from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)


class HeadlineCard(QFrame):

    def __init__(
        self,
        title="Bugünün En Önemli Gündemi",
        subtitle="AI tarafından analiz edilen en önemli gelişme burada gösterilecek.",
        category="Dünya"
    ):
        super().__init__()

        self.setObjectName("headlineCard")
        self.setMinimumHeight(180)

        self.setup_ui(title, subtitle, category)

    def setup_ui(self, title, subtitle, category):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Üst kısım (rozet + kategori)
        top_layout = QHBoxLayout()

        self.badge = QLabel("🔥 GÜNÜN MANŞETİ")
        self.badge.setObjectName("headlineBadge")

        self.category_label = QLabel(category)
        self.category_label.setObjectName("headlineCategory")

        top_layout.addWidget(self.badge)
        top_layout.addStretch()
        top_layout.addWidget(self.category_label)

        # Başlık
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("headlineTitle")

        # Alt başlık
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setObjectName("headlineSubtitle")

        layout.addLayout(top_layout)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)

    # Eski kullanım (geriye dönük uyumluluk için korunuyor)
    def set_text(self, title, subtitle, category):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.category_label.setText(category)

    # Yeni kullanım
    def set_data(self, headline):
        self.title_label.setText(headline.get("title", ""))
        self.subtitle_label.setText(headline.get("subtitle", ""))
        self.category_label.setText(headline.get("category", "Dünya"))