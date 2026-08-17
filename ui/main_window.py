from PySide6.QtWidgets import QMainWindow

from ui.video_news_page import VideoNewsPage
from ui.welcome_page import WelcomePage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NewsPilot AI")
        self.resize(1100, 750)

        self.current_page = None

        # Açılışta karşılama ekranı gösterilir
        self.show_welcome_page()

    def clear_page(self):
        if self.current_page:
            try:
                self.current_page.close()
            except RuntimeError:
                pass

            self.current_page.deleteLater()
            self.current_page = None

    def show_welcome_page(self):
        self.clear_page()
        self.welcome_page = WelcomePage()
        self.welcome_page.start_clicked.connect(self.show_video_page)
        self.current_page = self.welcome_page
        self.setCentralWidget(self.welcome_page)

    def show_video_page(self):
        self.clear_page()
        self.video_page = VideoNewsPage()
        self.current_page = self.video_page
        self.setCentralWidget(self.video_page)