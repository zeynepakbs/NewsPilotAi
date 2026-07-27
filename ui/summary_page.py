from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea
)

from PySide6.QtCore import Qt

from services.summary_service import SummaryService



class SummaryPage(QWidget):

    def __init__(self, back_callback):

        super().__init__()

        self.back_callback = back_callback

        self.summary_service = SummaryService()

        self.setup_ui()

        self.load_summary()



    def setup_ui(self):

        main_layout = QVBoxLayout(self)


        main_layout.setContentsMargins(
            40,
            30,
            40,
            30
        )


        # Geri butonu

        self.back_button = QPushButton(
            "← Geri"
        )

        self.back_button.clicked.connect(
            lambda: self.back_callback()
        )


        main_layout.addWidget(
            self.back_button
        )



        # Başlık

        title = QLabel(
            "🌍 Günlük AI Gündem Özeti"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setObjectName(
            "title"
        )


        main_layout.addWidget(
            title
        )



        # Scroll alanı

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )


        self.summary_label = QLabel(
            "AI özet hazırlanıyor..."
        )

        self.summary_label.setWordWrap(
            True
        )


        self.scroll.setWidget(
            self.summary_label
        )


        main_layout.addWidget(
            self.scroll
        )



    def load_summary(self):

        try:

            summary = self.summary_service.summarize_country(
                "tr"
            )


            self.summary_label.setText(
                summary
            )


        except Exception as e:

            self.summary_label.setText(
                f"Özet oluşturulamadı:\n{e}"
            )