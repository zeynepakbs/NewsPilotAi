class ImportanceCalculator:

    # 15 kanalda + Siyaset  -> 15 * 5  = 75  (kritik üst sınır)
    # 10 kanalda + Borsa    -> 10 * 3  = 30
    # Diğer kategoriler bu referans noktasına göre ölçeklendi.
    CATEGORY_WEIGHTS = {
        "Siyaset": 5,
        "Ekonomi": 5,
        "Afet": 5,
        "Sağlık": 4,
        "Teknoloji": 3,
        "Dünya": 3,
        "Borsa": 3,
        "Spor": 2,
        "Magazin": 1,
        "Diğer": 1,
    }

    KRITIK_MIN = 40
    KRITIK_MAX = 75

    def calculate(self, clusters):

        filtered = []

        for cluster in clusters:

            # AI haber değil dediyse çıkar
            if hasattr(cluster, "is_newsworthy"):
                if cluster.is_newsworthy is False:
                    continue

            weight = self.CATEGORY_WEIGHTS.get(
                cluster.category,
                1
            )

            # reliability_score = benzersiz kaynak sayısı * o kaynakların
            # güvenilirlik ağırlığı (RSS_SOURCES priority alanı).
            # Böylece hem "kaç kaynakta geçti" hem de "o kaynaklar ne kadar
            # güvenilir" aynı anda puana yansıyor.
            score = cluster.reliability_score * weight

            cluster.score = score

            # AgendaSelector importance_score'a göre sıralıyor,
            # ikisini senkron tutuyoruz.
            cluster.importance_score = score

            filtered.append(cluster)

        filtered.sort(
            key=lambda c: c.score,
            reverse=True
        )

        return filtered


    @classmethod
    def tier_for(cls, score):
        """
        Bir önem puanının hangi banda düştüğünü döndürür:
        'kritik' ya da None (gösterilmez).
        """

        if cls.KRITIK_MIN <= score <= cls.KRITIK_MAX:
            return "kritik"

        return None