from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath
from PySide6.QtWidgets import QWidget


class AvatarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        radius = min(width, height) * 0.45

        center_x = width / 2
        center_y = height / 2

        painter.fillRect(self.rect(), QColor(20, 22, 28))

        body_color = QColor(40, 44, 54)
        head_color = QColor(255, 255, 255)
        accent = QColor(58, 133, 255)

        painter.setBrush(QBrush(body_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            center_x - radius * 0.7,
            center_y - radius * 0.1,
            radius * 1.4,
            radius * 1.1,
            radius * 0.2,
            radius * 0.2,
        )

        painter.setBrush(QBrush(head_color))
        painter.drawEllipse(
            center_x - radius * 0.45,
            center_y - radius * 1.05,
            radius * 0.9,
            radius * 0.9,
        )

        painter.setBrush(QBrush(accent))
        painter.drawEllipse(
            center_x + radius * 0.15,
            center_y - radius * 0.75,
            radius * 0.16,
            radius * 0.16,
        )

        painter.setBrush(QBrush(QColor(255, 255, 255)))
        eye_radius = radius * 0.08
        painter.drawEllipse(
            center_x - radius * 0.18,
            center_y - radius * 0.95,
            eye_radius,
            eye_radius,
        )
        painter.drawEllipse(
            center_x + radius * 0.05,
            center_y - radius * 0.95,
            eye_radius,
            eye_radius,
        )

        painter.setBrush(QBrush(QColor(255, 110, 128)))
        painter.drawRoundedRect(
            center_x - radius * 0.25,
            center_y - radius * 0.7,
            radius * 0.5,
            radius * 0.12,
            radius * 0.08,
            radius * 0.08,
        )

        wave_path = QPainterPath()
        wave_path.moveTo(center_x - radius * 0.85, center_y + radius * 0.35)
        wave_path.cubicTo(
            center_x - radius * 0.5,
            center_y + radius * 0.55,
            center_x - radius * 0.2,
            center_y + radius * 0.15,
            center_x,
            center_y + radius * 0.35,
        )
        wave_path.cubicTo(
            center_x + radius * 0.2,
            center_y + radius * 0.55,
            center_x + radius * 0.55,
            center_y + radius * 0.2,
            center_x + radius * 0.85,
            center_y + radius * 0.35,
        )

        painter.setPen(QColor(113, 183, 255))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(wave_path)
