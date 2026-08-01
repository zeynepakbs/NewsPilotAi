from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
)


class PlayerControls(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("playerControlsOverlay")

        self.play_button = QPushButton("▶")
        self.pause_button = QPushButton("❚❚")
        self.stop_button = QPushButton("⏹")
        self.volume_label = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.progress = QSlider(Qt.Horizontal)
        self.fullscreen_button = QPushButton("⛶")

        self.play_button.setFixedSize(QSize(34, 34))
        self.pause_button.setFixedSize(QSize(34, 34))
        self.stop_button.setFixedSize(QSize(34, 34))
        self.fullscreen_button.setFixedSize(QSize(34, 34))
        self.volume_slider.setFixedSize(QSize(100, 24))
        self.progress.setFixedHeight(10)

        self.play_button.setCursor(Qt.PointingHandCursor)
        self.pause_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)

        self.play_button.setObjectName("playerControlButton")
        self.pause_button.setObjectName("playerControlButton")
        self.stop_button.setObjectName("playerControlButton")
        self.fullscreen_button.setObjectName("playerControlButton")
        self.progress.setObjectName("playerProgress")
        self.volume_slider.setObjectName("playerVolumeSlider")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        layout.addWidget(self.play_button)
        # keep pause_button for API compatibility but hide in UI (single toggle button used)
        self.pause_button.setVisible(False)
        # layout still reserves the space if needed; we don't add the pause button to the layout
        layout.addWidget(self.stop_button)
        layout.addWidget(self.progress, stretch=1)
        layout.addWidget(self.volume_label)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.fullscreen_button)

        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)

        # Ensure controls are enabled and have minimum sizes so they render
        self.play_button.setEnabled(True)
        self.play_button.setVisible(True)
        self.play_button.setMinimumSize(34, 34)

        # Basic styling for overlay controls to be visible on dark video
        self.setStyleSheet(
            """
            QWidget#playerControlsOverlay { background: transparent; }
            QPushButton#playerControlButton { color: white; }
            QSlider#playerProgress, QSlider#playerVolumeSlider { background: rgba(255,255,255,0.12); }
            """
        )
