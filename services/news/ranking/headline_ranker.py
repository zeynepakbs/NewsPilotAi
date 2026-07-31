from __future__ import annotations

from datetime import datetime
from typing import Optional

from services.news.ranking.headline_cluster import HeadlineCluster



class HeadlineRanker:


    def __init__(
        self,
        freshness_hours: int = 16
    ):

        self.freshness_hours = freshness_hours



    def _parse_published_at(
        self,
        published_at: str
    ) -> Optional[datetime]:

        if not published_at:
            return None


        text = published_at.strip()


        if text.endswith("Z"):

            text = text[:-1] + "+00:00"



        try:

            return datetime.fromisoformat(text)


        except ValueError:

            pass



        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):

            try:

                return datetime.strptime(
                    text,
                    fmt
                )


            except ValueError:

                continue



        return None



    def _freshness_score(
        self,
        cluster: HeadlineCluster
    ):


        dates = []


        for article in cluster.articles:


            date = self._parse_published_at(
                article.published_at
            )


            if date:

                dates.append(date)



        if not dates:

            return 0



        newest = max(dates)


        age_hours = (
            datetime.utcnow()
            - newest
        ).total_seconds() / 3600



        score = (
            self.freshness_hours - age_hours
        ) / self.freshness_hours



        return max(
            0,
            min(
                1,
                score
            )
        )



    def score(
        self,
        cluster: HeadlineCluster
    ):


        freshness = self._freshness_score(
            cluster
        )


        cluster.freshness_score = round(
            freshness,
            2
        )


        cluster.rank_score = round(

            (
                cluster.repeat_count * 5
            )

            +

            (
                cluster.source_count * 3
            )

            +

            freshness,

            2
        )


        return cluster



    def rank(
        self,
        clusters: list[HeadlineCluster]
    ):


        for cluster in clusters:

            self.score(cluster)



        return sorted(

            clusters,

            key=lambda cluster: (

                cluster.rank_score,

                cluster.source_count,

                cluster.repeat_count

            ),

            reverse=True

        )