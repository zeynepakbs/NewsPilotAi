from PySide6.QtWidgets import QMainWindow

from ui.video_news_page import VideoNewsPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NewsPilot AI")
        self.resize(1100, 750)

        self.current_page = None

        # Doğrudan video haber ekranı ile açılış
        self.show_video_page()

    def clear_page(self):
        if self.current_page:
            try:
                self.current_page.close()
            except RuntimeError:
                pass

            self.current_page.deleteLater()
            self.current_page = None

    def show_video_page(self):
        self.clear_page()
        self.video_page = VideoNewsPage()
        self.current_page = self.video_page
        self.setCentralWidget(self.video_page)