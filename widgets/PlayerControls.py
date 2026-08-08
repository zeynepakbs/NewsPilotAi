from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QStyle


class PlayerControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("playerControlsOverlay")

        self.download_button = QPushButton("Download")
        self.download_button.setFixedSize(QSize(95, 36))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setObjectName("playerControlButton")

        # Unicode ok karakteri ("⬇") yerine Qt'nin kendi standart ikonunu
        # kullanıyoruz. Bu, font/karakter setine bağımlı olmadığı için
        # platform bağımsız ve her zaman görünür bir ikon sağlar.
        self.download_button.setIcon(
            self.style().standardIcon(QStyle.SP_ArrowDown)
        )
        self.download_button.setIconSize(QSize(13, 13))

        # Başlangıçta pasif kalsın ama CSS ile görünürlüğünü ayarlayacağız
        self.download_button.setEnabled(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(self.download_button)

        self.setFixedHeight(50)

        self.setStyleSheet(
            """
            QWidget#playerControlsOverlay {
                background-color: transparent;
            }

            QPushButton#playerControlButton {
                background-color: rgba(0, 0, 0, 0.72);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
            }

            QPushButton#playerControlButton:hover {
                background-color: rgba(0, 0, 0, 0.9);
            }

            /* PASİF DURUM: buton tıklanamazken de görünür kalsın diye
               opaklığı öncekine göre artırdık (0.3 -> 0.55, 0.4 -> 0.75).
               Koyu video arka planında neredeyse görünmez olma sorunu
               buradan kaynaklanıyordu. */
            QPushButton#playerControlButton:disabled {
                background-color: rgba(0, 0, 0, 0.55);
                color: rgba(255, 255, 255, 0.75);
            }
            """
        )