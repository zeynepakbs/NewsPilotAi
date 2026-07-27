from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class NewsCard(QFrame):

    clicked = Signal()


    def __init__(self, title):

        super().__init__()


        self.setObjectName(
            "newsCard"
        )


        self.setCursor(
            Qt.PointingHandCursor
        )


        self.setMinimumHeight(
            170
        )


        layout = QVBoxLayout(
            self
        )


        layout.setSpacing(
            10
        )


        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )


        self.label = QLabel(
            title
        )


        self.label.setAlignment(
            Qt.AlignCenter
        )


        self.label.setWordWrap(
            True
        )


        layout.addStretch()


        layout.addWidget(
            self.label
        )


        layout.addStretch()



    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.clicked.emit()


        super().mousePressEvent(
            event
        )