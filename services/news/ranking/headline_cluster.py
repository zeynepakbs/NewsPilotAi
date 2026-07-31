from dataclasses import dataclass

from services.news.models.article import Article



@dataclass
class HeadlineCluster:


    title: str

    articles: list[Article]


    score: int = 0


    category: str | None = None


    is_newsworthy: bool = True


    importance_score: int = 0


    summary: str = ""



    @property
    def source_count(self):

        return len(
            {
                article.source
                for article in self.articles
                if article.source
            }
        )


    @property
    def repeat_count(self):

        return len(self.articles)


    @property
    def sources(self):

        return list(
            {
                article.source
                for article in self.articles
                if article.source
            }
        )


    @property
    def reliability_score(self):
        """
        Sadece kaç kaynakta geçtiğine değil, o kaynakların
        güvenilirliğine (RSS_SOURCES'taki 'priority' alanı,
        1-5 arası) göre de ağırlıklandırılmış toplam puan.

        Aynı kaynaktan gelen tekrarlar bir kez sayılır; her
        benzersiz kaynağın en yüksek priority değeri kullanılır.

        Normalizasyon: priority'nin nötr/ortalama değeri 3 kabul
        edilip toplam 3'e bölünür. Böylece N kaynağın hepsi
        priority=3 (ortalama güven) olduğunda reliability_score eski
        source_count ile aynı çıkar; daha güvenilir kaynaklar puanı
        yukarı, daha az güvenilir kaynaklar aşağı çeker. Bu sayede
        ImportanceCalculator'daki KRITIK_MIN/MAX eşikleri eskisiyle
        aynı skalada kalmaya devam eder.
        """

        best_priority_by_source = {}

        for article in self.articles:

            if not article.source:
                continue

            priority = getattr(article, "priority", 1) or 1

            current = best_priority_by_source.get(article.source, 0)

            if priority > current:
                best_priority_by_source[article.source] = priority

        if not best_priority_by_source:
            return 0

        NEUTRAL_PRIORITY = 3

        return round(
            sum(best_priority_by_source.values()) / NEUTRAL_PRIORITY,
            2
        )


    @property
    def avg_reliability(self):
        """0 (kaynak yok) ile 5 (tüm kaynaklar en üst güven seviyesi) arası ortalama."""

        if not self.source_count:
            return 0

        return round(self.reliability_score / self.source_count, 2)