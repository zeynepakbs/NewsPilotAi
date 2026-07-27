from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QPushButton,
)

from PySide6.QtCore import Qt, Signal


class SummaryCard(QFrame):

    refresh_requested = Signal()

    def __init__(self, summary="Bugünün AI özeti henüz oluşturulmadı."):
        super().__init__()

        self.setObjectName("summaryCard")

        self.setup_ui(summary)

    def setup_ui(self, summary):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        

        title = QLabel("🧠 AI Günlük Özeti")
        title.setObjectName("summaryTitle")

       

        self.summary_label = QLabel(summary)
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignTop)
        self.summary_label.setObjectName("summaryText")

    

        layout.addWidget(title)
        layout.addWidget(self.summary_label)
        layout.addStretch()
        

    def set_summary(self, summary: str):
        self.summary_label.setText(summary)