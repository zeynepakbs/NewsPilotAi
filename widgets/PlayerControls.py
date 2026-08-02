from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider


class PlayerControls(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("playerControlsOverlay")

        # Butonlar
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(QSize(45, 45))
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setObjectName("playerControlButton")

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setCursor(Qt.PointingHandCursor)

        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setFixedSize(QSize(45, 45))
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.setObjectName("playerControlButton")

        # Yerleşim
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        layout.addWidget(self.play_button)
        layout.addWidget(self.volume_slider)
        layout.addStretch()
        layout.addWidget(self.fullscreen_button)

        self.setFixedHeight(65)

        # Stil Tanımlamaları
        self.setStyleSheet(
            """
            QWidget#playerControlsOverlay {
                background-color: rgba(0, 0, 0, 0.6);
                border-radius: 12px;
            }
            QPushButton#playerControlButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton#playerControlButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            """
        )