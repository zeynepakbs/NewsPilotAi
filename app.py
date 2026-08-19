import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow
from license.license_store import load_license_key
from license.license_check import check_license
from license.license_dialog import LicenseDialog
from paths import STYLE_QSS, ensure_runtime_dirs


def load_styles(app):
    if STYLE_QSS.exists():
        with open(STYLE_QSS, "r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())



def ensure_license() -> bool:
    saved_key = load_license_key()

    if saved_key:
        ok, msg = check_license(saved_key)
        if ok:
            return True
        dialog = LicenseDialog(error_message=msg)
        dialog.exec()
        return dialog.activated
    else:
        dialog = LicenseDialog()
        dialog.exec()
        return dialog.activated


def main():
    ensure_runtime_dirs()
    app = QApplication(sys.argv)

    load_styles(app)

    if not ensure_license():
        QMessageBox.information(
            None, "NewsPilot", "Lisans doğrulanamadı. Uygulama kapatılıyor."
        )
        sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()