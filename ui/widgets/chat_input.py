from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton


class ChatInput(QWidget):

    message_sent = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Bugün dünyada neler oldu?")

        self.send_button = QPushButton("➜")
        self.send_button.setFixedSize(45, 45)

        layout.addWidget(self.input)
        layout.addWidget(self.send_button)

        self.send_button.clicked.connect(self.send_message)
        self.input.returnPressed.connect(self.send_message)

    def send_message(self):
        text = self.input.text().strip()

        if not text:
            return

        self.message_sent.emit(text)
        self.input.clear()