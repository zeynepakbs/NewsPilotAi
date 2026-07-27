import requests

from config import GNEWS_API_KEY



class NewsService:


    BASE_URL = "https://gnews.io/api/v4/top-headlines"



    COUNTRY_LANG = {

        "tr": "tr",

        "us": "en",

        "gb": "en",

        "de": "de",

        "fr": "fr",

        "it": "it",

        "es": "es",

        "nl": "nl",

    }




    def get_news(self, country="tr", max_results=10):


        language = self.COUNTRY_LANG.get(
            country,
            "en"
        )


        params = {

            "country": country,

            "lang": language,

            "max": max_results,

            "apikey": GNEWS_API_KEY,

        }



        try:


            response = requests.get(

                self.BASE_URL,

                params=params,

                timeout=10

            )


            response.raise_for_status()



            data = response.json()



            articles = data.get(
                "articles",
                []
            )



            return articles



        except Exception as e:


            raise Exception(

                f"Haber servisi hatası: {e}"

            )