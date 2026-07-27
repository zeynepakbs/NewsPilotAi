import time
import json
import os
import hashlib

import requests

from config import GNEWS_API_KEY


class NewsService:

    BASE_URL = "https://gnews.io/api/v4/top-headlines"

    CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "_cache")
    CACHE_TTL_SECONDS = 15 * 60  # 15 dakika

    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _cache_path(self, params):
        # apikey'i cache anahtarından çıkar (hassas veri dosya adında olmasın)
        key_params = {k: v for k, v in params.items() if k != "apikey"}
        key_str = json.dumps(key_params, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode("utf-8")).hexdigest()
        return os.path.join(self.CACHE_DIR, f"news_{key_hash}.json")

    def _read_cache(self, params):
        path = self._cache_path(params)

        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            age = time.time() - cached.get("timestamp", 0)

            if age > self.CACHE_TTL_SECONDS:
                return None

            return cached.get("articles")

        except (json.JSONDecodeError, OSError):
            return None

    def _write_cache(self, params, articles):
        path = self._cache_path(params)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {"timestamp": time.time(), "articles": articles},
                    f,
                    ensure_ascii=False,
                )
        except OSError:
            pass  # Cache yazılamazsa sessizce geç, kritik değil

    def _fetch(self, params, lang_tag, retries=2, backoff=5):

        cached = self._read_cache(params)
        if cached is not None:
            return cached

        for attempt in range(retries + 1):
            try:
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=10,
                )

                if response.status_code == 429:
                    if attempt < retries:
                        time.sleep(backoff * (attempt + 1))
                        continue
                    raise Exception(
                        "GNews API istek limitine ulaşıldı (429). "
                        "Lütfen birkaç dakika bekleyip tekrar deneyin."
                    )

                response.raise_for_status()

                data = response.json()
                raw_articles = data.get("articles", [])

                articles = [
                    {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "url": article.get("url", ""),
                        "image": article.get("image", ""),
                        "published_at": article.get("publishedAt", ""),
                        "lang": lang_tag,
                    }
                    for article in raw_articles
                ]

                self._write_cache(params, articles)

                return articles

            except requests.RequestException as e:
                if attempt < retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise Exception(f"Haberler alınamadı: {e}")

    def get_global_news(self, language="en", max_results=14):
        params = {
            "lang": language,
            "max": max_results,
            "apikey": GNEWS_API_KEY,
        }
        return self._fetch(params, lang_tag="en")

    def get_turkey_news(self, language="tr", max_results=6):
        params = {
            "lang": language,
            "country": "tr",
            "max": max_results,
            "apikey": GNEWS_API_KEY,
        }
        return self._fetch(params, lang_tag="tr")

    def get_combined_news(self, global_count=14, turkey_count=6):
        turkey_articles = self.get_turkey_news(max_results=turkey_count)

        # İki istek arasında küçük bir bekleme (cache boşsa) 429 riskini azaltır
        time.sleep(1)

        global_articles = self.get_global_news(max_results=global_count)

        return turkey_articles + global_articles