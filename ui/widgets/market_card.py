from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)


class MarketCard(QFrame):

    def __init__(self, markets=None):
        super().__init__()

        if markets is None:
            markets = []

        self.setObjectName("marketCard")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        title = QLabel("💹 Piyasalar")
        title.setObjectName("marketTitle")

        self.layout.addWidget(title)

        self.markets_layout = QVBoxLayout()
        self.markets_layout.setSpacing(10)

        self.layout.addLayout(self.markets_layout)

        self.set_markets(markets)

    def clear_markets(self):

        while self.markets_layout.count():

            item = self.markets_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

    def set_markets(self, markets):

        self.clear_markets()

        for market in markets:

            row = QHBoxLayout()
            row.setSpacing(10)

            name = QLabel(market["name"])
            name.setObjectName("marketName")

            value = QLabel(market["value"])
            value.setObjectName("marketValue")

            change = QLabel(market["change"])
            change.setMinimumWidth(60)

            if market["change"].startswith("-"):
                change.setObjectName("marketDown")
            else:
                change.setObjectName("marketUp")

            row.addWidget(name)
            row.addStretch()
            row.addWidget(value)
            row.addWidget(change)

            self.markets_layout.addLayout(row)