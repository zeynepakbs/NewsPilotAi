class NewsRanker:


    MIN_SCORE = 20


    def rank_news(self, clusters):


        if not clusters:
            return []



        filtered = []



        for cluster in clusters:


            # AI analizinden gelen kontrol

            if hasattr(cluster, "is_newsworthy"):


                if not cluster.is_newsworthy:
                    continue



            # Çok düşük puanlı haberleri ele

            if cluster.score < self.MIN_SCORE:
                continue



            filtered.append(
                cluster
            )



        filtered.sort(

            key=lambda x: (

                x.score,

                x.source_count

            ),

            reverse=True

        )



        return filtered[:10]