from services.news.ai.gemini_client import OpenAIClient
from services.news.ai.prompt_builder import PromptBuilder


class NewsAnalyzer:

    MAX_AI_ANALYSIS = 10

    def __init__(self):

        self.client = OpenAIClient()


    def analyze(self, cluster):

        sources = sorted(
            {
                article.source
                for article in cluster.articles
                if article.source
            }
        )

        prompt = PromptBuilder.build_analysis_prompt(
            cluster=cluster,
            sources=sources
        )

        response = self.client.ask(
            prompt
        )

        return self.client.parse_json(
            response
        )


    def apply_analysis(
        self,
        cluster,
        analysis
    ):

        cluster.summary = analysis.get(
            "summary",
            ""
        )

        cluster.is_newsworthy = analysis.get(
            "is_newsworthy",
            True
        )

        cluster.importance_score = analysis.get(
            "importance_score",
            cluster.score
        )

        ai_category = analysis.get(
            "category"
        )

        if ai_category:
            cluster.category = ai_category

        return cluster


    def _preliminary_rank(self, clusters):
        """
        AI kullanmadan önce tekrar sayısına göre ön sıralama.
        """

        return sorted(
            clusters,
            key=lambda c: c.source_count,
            reverse=True
        )


    def analyze_all(
        self,
        clusters,
        max_ai_analysis=None
    ):

        if max_ai_analysis is None:
            max_ai_analysis = self.MAX_AI_ANALYSIS

        ranked = self._preliminary_rank(
            clusters
        )

        to_analyze = ranked[:max_ai_analysis]
        skipped = ranked[max_ai_analysis:]

        results = []

        for cluster in to_analyze:

            try:

                analysis = self.analyze(
                    cluster
                )

                cluster = self.apply_analysis(
                    cluster,
                    analysis
                )

                results.append(
                    cluster
                )

            except Exception as e:

                print(
                    "[NewsAnalyzer]",
                    f"Analiz başarısız: {cluster.title} -> {e}"
                )

                cluster.summary = getattr(
                    cluster,
                    "summary",
                    ""
                )

                cluster.is_newsworthy = True

                cluster.importance_score = cluster.score

                results.append(
                    cluster
                )

        for cluster in skipped:

            cluster.summary = getattr(
                cluster,
                "summary",
                ""
            )

            cluster.is_newsworthy = True

            results.append(
                cluster
            )

        return results