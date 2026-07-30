from collections import Counter, defaultdict


class AgendaSelector:


    def __init__(self, max_per_region=10):

        self.max_per_region = max_per_region


    def _resolve_region(self, cluster):

        regions = [
            article.region
            for article in cluster.articles
            if getattr(article, "region", "")
        ]

        if not regions:
            return ""

        return Counter(regions).most_common(1)[0][0]


    def _cluster_to_dict(self, cluster, region):

        return {

            "title": getattr(cluster, "title", ""),

            "summary": getattr(cluster, "summary", ""),

            "category": getattr(cluster, "category", "") or "",

            "region": region,

            "importance": getattr(cluster, "importance_score", 0),

            "repeat_count": getattr(cluster, "repeat_count", 1),

            "sources": getattr(cluster, "sources", [])

        }


    def select(self, clusters):

        by_region = defaultdict(list)

        for cluster in clusters:

            region = self._resolve_region(cluster)
            by_region[region].append(cluster)


        selected = []

        for region, region_clusters in by_region.items():

            region_clusters = sorted(
                region_clusters,
                key=lambda c: getattr(c, "importance_score", 0),
                reverse=True
            )

            for cluster in region_clusters[:self.max_per_region]:

                selected.append(
                    self._cluster_to_dict(cluster, region)
                )

        return selected