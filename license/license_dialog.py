from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from .license_check import check_license
from .license_store import save_license_key

class LicenseDialog(QDialog):
    def __init__(self, parent=None, error_message: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("NewsPilot - Lisans Aktivasyonu")
        self.setFixedSize(400, 180)
        self.activated = False

        layout = QVBoxLayout(self)

        if error_message:
            warn = QLabel(error_message)
            warn.setStyleSheet("color: red;")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        layout.addWidget(QLabel("Lisans anahtarınızı girin:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("NP-2026-XXXX-XXXX")
        layout.addWidget(self.key_input)

        self.activate_btn = QPushButton("Aktive Et")
        self.activate_btn.clicked.connect(self._on_activate)
        layout.addWidget(self.activate_btn)

    def _on_activate(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Hata", "Lütfen bir lisans anahtarı girin.")
            return

        ok, msg = check_license(key)
        if ok:
            save_license_key(key)
            self.activated = True
            self.accept()
        else:
            QMessageBox.critical(self, "Aktivasyon Başarısız", msg)