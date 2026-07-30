from enum import Enum

from services.news.ranking.headline_cluster import HeadlineCluster


class Category(Enum):

    POLITICS = "Siyaset"
    ECONOMY = "Ekonomi"
    MARKET = "Borsa"
    SPORT = "Spor"
    MAGAZINE = "Magazin"
    HEALTH = "Sağlık"
    TECHNOLOGY = "Teknoloji"
    DISASTER = "Afet"
    WORLD = "Dünya"
    OTHER = "Diğer"



class CategoryClassifier:


    KEYWORDS = {


        Category.DISASTER: [

            "deprem",
            "zelzele",
            "afet",
            "yangın",
            "sel",
            "fırtına",
            "kasırga",
            "heyelan",
            "tsunami"

        ],



        Category.POLITICS: [

            "cumhurbaşkanı",
            "erdoğan",
            "trump",
            "bakan",
            "bakanlık",
            "seçim",
            "parlamento",
            "meclis",
            "senato",
            "başkan",
            "hükümet",
            "dışişleri"

        ],



        Category.ECONOMY: [

            "ekonomi",
            "enflasyon",
            "faiz",
            "vergi",
            "gdp",
            "büyüme",
            "işsizlik",
            "merkez bankası",
            "ticaret",
            "ihracat",
            "ithalat"

        ],



        Category.MARKET: [

            "borsa",
            "hisse",
            "bitcoin",
            "ethereum",
            "dolar",
            "euro",
            "altın",
            "nasdaq",
            "sp500"

        ],



        Category.SPORT: [

            "futbol",
            "maç",
            "gol",
            "uefa",
            "fifa",
            "şampiyonlar ligi",
            "transfer",
            "galatasaray",
            "fenerbahçe"

        ],



        Category.HEALTH: [

            "sağlık",
            "hastane",
            "virüs",
            "salgın",
            "aşı",
            "kanser",
            "hastalık"

        ],



        Category.TECHNOLOGY: [

            "yapay zeka",
            "ai",
            "apple",
            "google",
            "microsoft",
            "openai",
            "çip",
            "robot"

        ],



        Category.MAGAZINE: [

            "oyuncu",
            "şarkıcı",
            "film",
            "dizi",
            "ünlü"

        ],
        Category.DISASTER:[
            "deprem",
               "sel",
            "yangın",
            "fırtına",
           "kasırga",
            "afet",
           "tsunami",
            "volkan"
        ]

    }



    def classify(
        self,
        clusters:list[HeadlineCluster]
    ):


        for cluster in clusters:


            text = cluster.title.lower()



            for category, keywords in self.KEYWORDS.items():


                if any(
                    keyword in text
                    for keyword in keywords
                ):

                    cluster.category = category.value
                    break



            else:

                cluster.category = Category.WORLD.value



        return clusters