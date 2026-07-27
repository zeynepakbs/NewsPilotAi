from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
)

from ui.widgets.news_card import NewsCard
from ui.widgets.summary_card import SummaryCard



class HomePage(QWidget):

    news_requested = Signal(str)



    def __init__(self):

        super().__init__()

        self.setup_ui()





    def setup_ui(self):

        main_layout = QVBoxLayout(self)


        main_layout.setAlignment(
            Qt.AlignTop
        )


        main_layout.setSpacing(
            25
        )


        main_layout.setContentsMargins(
            80,
            40,
            80,
            40
        )



        # Logo

        logo = QLabel(
            "🌍"
        )


        logo.setAlignment(
            Qt.AlignCenter
        )


        logo.setObjectName(
            "logo"
        )





        # Başlık

        title = QLabel(
            "NewsPilot AI"
        )


        title.setAlignment(
            Qt.AlignCenter
        )


        title.setObjectName(
            "title"
        )





        # Alt başlık

        subtitle = QLabel(
            "Dünyada bugün neler oluyor?"
        )


        subtitle.setAlignment(
            Qt.AlignCenter
        )


        subtitle.setObjectName(
            "subtitle"
        )





        # Haber kartları

        cards_layout = QGridLayout()


        cards_layout.setSpacing(
            20
        )




        self.usa_card = NewsCard(
            "🇺🇸 Amerika"
        )


        self.europe_card = NewsCard(
            "🇪🇺 Avrupa"
        )


        self.turkey_card = NewsCard(
            "🇹🇷 Türkiye"
        )


        self.summary_card = SummaryCard()





        # Kart bağlantıları


        self.usa_card.clicked.connect(
            lambda: self.news_requested.emit("us")
        )


        self.europe_card.clicked.connect(
            lambda: self.news_requested.emit("de")
        )


        self.turkey_card.clicked.connect(
            lambda: self.news_requested.emit("tr")
        )


        self.summary_card.clicked.connect(
            lambda: self.news_requested.emit("summary")
        )





        cards_layout.addWidget(
            self.usa_card,
            0,
            0
        )


        cards_layout.addWidget(
            self.europe_card,
            0,
            1
        )


        cards_layout.addWidget(
            self.turkey_card,
            1,
            0
        )


        cards_layout.addWidget(
            self.summary_card,
            1,
            1
        )





        # Ana layout


        main_layout.addWidget(
            logo
        )


        main_layout.addWidget(
            title
        )


        main_layout.addWidget(
            subtitle
        )


        main_layout.addSpacing(
            40
        )


        main_layout.addLayout(
            cards_layout
        )


        main_layout.addStretch()