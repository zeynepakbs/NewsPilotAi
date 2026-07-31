from PySide6.QtWidgets import QMainWindow

from ui.home_page import HomePage
from ui.critical_page import CriticalNewsPage




class MainWindow(QMainWindow):


    def __init__(self):

        super().__init__()


        self.setWindowTitle(
            "NewsPilot AI"
        )


        self.resize(
            1100,
            750
        )


        self.current_page = None


        self.show_home_page()



    def clear_page(self):

        if self.current_page:

            try:

                self.current_page.close()

            except RuntimeError:

                pass


            self.current_page.deleteLater()

            self.current_page = None



    def show_home_page(self):

        self.clear_page()

        self.home_page = HomePage()

        self.current_page = self.home_page

        self.setCentralWidget(
            self.home_page
        )



    def show_critical_page(self):

        self.clear_page()

        self.critical_page = CriticalNewsPage(
            back_callback=self.show_home_page
        )

        self.current_page = self.critical_page

        self.setCentralWidget(
            self.critical_page
        )



