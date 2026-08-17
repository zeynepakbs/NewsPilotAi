from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)


class WelcomePage(QWidget):

    start_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("welcomePage")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet(
            """
            QWidget#welcomePage {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #05060a,
                    stop: 0.55 #0b0f1a,
                    stop: 1 #0d1420
                );
            }

            QFrame#logoBadge {
                background-color: rgba(59, 130, 246, 0.14);
                border: 1px solid rgba(59, 130, 246, 0.35);
                border-radius: 36px;
            }

            QLabel#logoLetter {
                color: #60a5fa;
                font-size: 30px;
                font-weight: 700;
                background: transparent;
            }

            QLabel#eyebrow {
                color: #60a5fa;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 3px;
                background: transparent;
            }

            QLabel#welcomeTitle {
                color: #f5f7fa;
                font-size: 34px;
                font-weight: 700;
                background: transparent;
            }

            QLabel#welcomeSubtitle {
                color: #8b93a3;
                font-size: 14px;
                background: transparent;
            }

            QPushButton#startButton {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 15px 46px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton#startButton:hover {
                background-color: #2f6fe0;
            }

            QPushButton#startButton:pressed {
                background-color: #1d4ed8;
            }

            QLabel#footerLabel {
                color: #4b5566;
                font-size: 11px;
                background: transparent;
            }
            """
        )

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)
        outer_layout.setSpacing(0)

        # --- Logo rozeti ---
        logo_badge = QFrame()
        logo_badge.setObjectName("logoBadge")
        logo_badge.setFixedSize(72, 72)
        logo_layout = QVBoxLayout(logo_badge)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_letter = QLabel("N")
        logo_letter.setObjectName("logoLetter")
        logo_letter.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_letter)

        # --- Üst etiket ---
        eyebrow = QLabel("YAPAY ZEKA DESTEKLİ HABER STÜDYOSU")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)

        # --- Başlık ---
        title = QLabel("NewsPilot AI'a Hoş Geldiniz")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        # --- Alt açıklama ---
        subtitle = QLabel("Güncel haberleri otomatik olarak derleyip video haline getirir.")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        # --- Başla butonu ---
        start_button = QPushButton("Başla")
        start_button.setObjectName("startButton")
        start_button.setCursor(Qt.PointingHandCursor)
        start_button.clicked.connect(self.start_clicked.emit)

        # --- Alt bilgi ---
        footer = QLabel("NewsPilot AI  ·  Sürüm 1.0")
        footer.setObjectName("footerLabel")
        footer.setAlignment(Qt.AlignCenter)

        outer_layout.addStretch(3)
        outer_layout.addWidget(logo_badge, alignment=Qt.AlignCenter)
        outer_layout.addSpacing(22)
        outer_layout.addWidget(eyebrow)
        outer_layout.addSpacing(10)
        outer_layout.addWidget(title)
        outer_layout.addSpacing(10)
        outer_layout.addWidget(subtitle)
        outer_layout.addSpacing(32)
        outer_layout.addWidget(start_button, alignment=Qt.AlignCenter)
        outer_layout.addStretch(2)
        outer_layout.addWidget(footer)
        outer_layout.addSpacing(24)