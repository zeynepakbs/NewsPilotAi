import time
import json
import os
import requests


class MarketService:

    CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "_cache")
    CACHE_FILE = os.path.join(CACHE_DIR, "market_history.json")
    CACHE_TTL_SECONDS = 5 * 60  # 5 dakika

    FRANKFURTER_URL = "https://api.frankfurter.app/latest"
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _load_history(self):
        if not os.path.exists(self.CACHE_FILE):
            return {}

        try:
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_history(self, history):
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False)
        except OSError:
            pass

    def _calc_change(self, history, key, current_value):
        entry = history.get(key)
        now = time.time()

        change_str = "0.00%"

        if entry and entry.get("value"):
            previous_value = entry["value"]
            if previous_value:
                diff = (current_value - previous_value) / previous_value * 100
                sign = "+" if diff >= 0 else ""
                change_str = f"{sign}{diff:.2f}%"

        history[key] = {"value": current_value, "timestamp": now}

        return change_str

    def _fetch_forex(self):
        response = requests.get(
            self.FRANKFURTER_URL,
            params={"from": "USD", "to": "TRY,EUR"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        usd_try = data["rates"]["TRY"]

        # EUR/TRY için: USD->EUR ve USD->TRY oranlarından türetiyoruz
        usd_eur = data["rates"]["EUR"]
        eur_try = usd_try / usd_eur

        return usd_try, eur_try

    def _fetch_bitcoin_try(self):
        response = requests.get(
            self.COINGECKO_URL,
            params={"ids": "bitcoin", "vs_currencies": "try"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return data["bitcoin"]["try"]

    def get_market_data(self):

        history = self._load_history()

        try:
            usd_try, eur_try = self._fetch_forex()
        except requests.RequestException:
            usd_try, eur_try = None, None

        try:
            btc_try = self._fetch_bitcoin_try()
        except requests.RequestException:
            btc_try = None

        markets = []

        if usd_try is not None:
            change = self._calc_change(history, "USD_TRY", usd_try)
            markets.append({
                "name": "USD/TRY",
                "value": f"{usd_try:.2f}",
                "change": change,
            })

        if eur_try is not None:
            change = self._calc_change(history, "EUR_TRY", eur_try)
            markets.append({
                "name": "EUR/TRY",
                "value": f"{eur_try:.2f}",
                "change": change,
            })

        if btc_try is not None:
            change = self._calc_change(history, "BTC_TRY", btc_try)
            markets.append({
                "name": "Bitcoin",
                "value": f"₺{btc_try:,.0f}",
                "change": change,
            })

        self._save_history(history)

        if not markets:
            # Hiçbir API'ye ulaşılamazsa, uygulama çökmesin diye yedek veri
            markets = [
                {"name": "USD/TRY", "value": "—", "change": "0.00%"},
                {"name": "EUR/TRY", "value": "—", "change": "0.00%"},
                {"name": "Bitcoin", "value": "—", "change": "0.00%"},
            ]

        return markets