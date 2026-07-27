from PySide6.QtWidgets import QMainWindow

from ui.home_page import HomePage
from ui.news_page import NewsPage
from ui.summary_page import SummaryPage




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


        self.home_page.news_requested.connect(
            self.open_news_page
        )


        self.current_page = self.home_page



        self.setCentralWidget(
            self.home_page
        )








    def open_news_page(self, country):


        print(
            f"Açılan sayfa: {country}"
        )


        self.clear_page()




        if country == "summary":


            self.summary_page = SummaryPage(
                self.show_home_page
            )


            self.current_page = self.summary_page



            self.setCentralWidget(
                self.summary_page
            )


            return






        self.news_page = NewsPage(
            country,
            self.show_home_page
        )


        self.current_page = self.news_page



        self.setCentralWidget(
            self.news_page
        )