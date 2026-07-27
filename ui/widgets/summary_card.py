from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout
)

from PySide6.QtCore import Qt, Signal



class SummaryCard(QFrame):

    clicked = Signal()


    def __init__(self):

        super().__init__()


        self.setObjectName(
            "summaryCard"
        )


        self.setCursor(
            Qt.PointingHandCursor
        )


        layout = QVBoxLayout(self)


        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )


        self.title = QLabel(
            "🌍 Günlük Özet"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )


        self.summary_label = QLabel(
            "AI özet hazırlanıyor..."
        )


        self.summary_label.setWordWrap(
            True
        )


        layout.addWidget(
            self.title
        )


        layout.addWidget(
            self.summary_label
        )



    def mousePressEvent(self, event):

        self.clicked.emit()


        super().mousePressEvent(
            event
        )



    def update_summary(self, text):

        self.summary_label.setText(
            text
        )