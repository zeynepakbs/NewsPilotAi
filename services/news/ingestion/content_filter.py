import re


class ContentFilter:

    # Gerçek haber olmayan, otomatik üretilen,
    # widget / yayın / liste / şablon içerikleri
    # embedding öncesinde temizlenir.
    BOILERPLATE_PATTERNS = [

        # =========================
        # Deprem widget içerikleri
        # =========================
        r"deprem mi oldu",
        r"son depremler",
        r"kandilli ve afad",


        # =========================
        # Tarif / otomatik içerik
        # =========================
        r"\btarifi\b",
        r"\(lu\)\s*$",


        # =========================
        # Canlı yayın / bülten içerikleri
        # =========================
        r"\blive\b",
        r"canlı yayın",
        r"canli yayin",

        r"news bulletin",
        r"latest news bulletin",
        r"breaking news live",

        r"evening news",
        r"morning news",
        r"midday",

        r"abc news live",
        r"bbc news app",
        r"cbs evening news",


        # =========================
        # Günlük özet / haber akışı
        # =========================
        r"bugün ne oldu",
        r"bugun ne oldu",

        r"günün haberleri",
        r"gunun haberleri",

        r"haber bülteni",
        r"haber bulteni",

        r"gündemden son haberler",
        r"gundemden son haberler",

        r"son dakika haberleri",


        # =========================
        # TV / program akışı
        # =========================
        r"tv yayın akışı",
        r"tv yayin akisi",

        r"program akışı",
        r"program akisi",

        r"yayın akışı",
        r"yayin akisi",
    ]


    _compiled_patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in BOILERPLATE_PATTERNS
    ]


    @classmethod
    def is_boilerplate(cls, title: str) -> bool:
        """
        Başlığın otomatik içerik / widget olup olmadığını kontrol eder.
        """

        if not title:
            return False

        return any(
            pattern.search(title)
            for pattern in cls._compiled_patterns
        )


    @staticmethod
    def _normalize_for_dedup(title: str) -> str:
        """
        Aynı başlığa sahip RSS tekrarlarını yakalamak için
        normalize eder.
        """

        if not title:
            return ""

        text = title.lower().strip()

        # Fazla boşlukları temizle
        text = re.sub(r"\s+", " ", text)

        return text


    @classmethod
    def filter_articles(cls, articles):
        """
        Filtre sırası:

        1) Otomatik widget / bülten / yayın içeriklerini siler.
        2) Aynı başlığa sahip RSS tekrarlarını temizler.
        3) Daha yüksek priority olan kaynağı tutar.

        Embedding hesaplamasından ÖNCE çalışmalıdır.
        """

        seen = {}


        for article in articles:

            # 1) Gürültü filtreleme
            if cls.is_boilerplate(article.title):
                continue


            # 2) Başlık kontrolü
            key = cls._normalize_for_dedup(
                article.title
            )


            if not key:
                continue


            existing = seen.get(key)


            # İlk defa görüyorsak ekle
            if existing is None:

                seen[key] = article
                continue


            # Aynı haber tekrar geldiyse
            # daha kaliteli kaynağı tut
            if getattr(article, "priority", 0) > getattr(existing, "priority", 0):

                seen[key] = article


        return list(seen.values())