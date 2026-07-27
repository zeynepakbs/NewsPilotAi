from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtCore import Qt

from ui.widgets.flow_layout import FlowLayout


class TrendCard(QFrame):

    def __init__(self, title="🔥 Trend Konular", trends=None):
        super().__init__()

        if trends is None:
            trends = []

        self.setObjectName("trendCard")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setObjectName("trendTitle")

        self.layout.addWidget(title_label)

        self.tags_widget = QWidget()
        self.tags_layout = FlowLayout(self.tags_widget, margin=0, h_spacing=8, v_spacing=8)

        self.layout.addWidget(self.tags_widget)

        self.set_trends(trends)

    def clear_tags(self):

        while self.tags_layout.count():

            item = self.tags_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

    def set_trends(self, trends):

        self.clear_tags()

        for trend in trends:

            chip = QLabel(f"#{trend}")

            chip.setObjectName("trendChip")

            chip.setAlignment(Qt.AlignCenter)

            self.tags_layout.addWidget(chip)