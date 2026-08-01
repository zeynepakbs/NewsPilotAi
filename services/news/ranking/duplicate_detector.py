import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from services.news.models.article import Article
from services.news.ranking.headline_cluster import HeadlineCluster
from services.news.ranking.entity_detector import EntityDetector

from dateutil import parser as date_parser


class DuplicateDetector:

    TITLE_WEIGHT = 0.8
    DESCRIPTION_WEIGHT = 0.2
    DEFAULT_THRESHOLD = 0.52
    MAX_DAY_DIFF = 3

    def __init__(self):
        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.embedding_cache = {}
        self.entity_detector = EntityDetector()

    def _parse_date(self, published_at):
        if not published_at:
            return None
        
        try:
            return date_parser.parse(published_at)
        except Exception:
            return None

    def _within_date_window(self, date1, date2):
        if not date1 or not date2:
            return True
        
        return abs((date1 - date2).days) <= self.MAX_DAY_DIFF

    def _encode(self, texts):
        if not texts:
            return torch.tensor([])

        embeddings = [None] * len(texts)
        texts_to_encode = []
        indices_to_encode = []

        for i, text in enumerate(texts):
            if text in self.embedding_cache:
                embeddings[i] = self.embedding_cache[text]
            else:
                texts_to_encode.append(text)
                indices_to_encode.append(i)

        if texts_to_encode:
            new_embs = self.model.encode(
                texts_to_encode,
                convert_to_tensor=True,
                normalize_embeddings=True,
                batch_size=64,
                show_progress_bar=False
            )
            
            for idx, emb, text in zip(indices_to_encode, new_embs, texts_to_encode):
                embeddings[idx] = emb
                self.embedding_cache[text] = emb

        return torch.stack(embeddings)

    def _choose_title(self, articles):
        return max(
            articles,
            key=lambda a: (
                getattr(a, "priority", 0),
                len(a.title or "")
            )
        ).title

    def remove_duplicates(
        self,
        articles: list[Article],
        threshold=None
    ):
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD

        titles = [a.title or "" for a in articles]
        descriptions = [a.description or "" for a in articles]

        title_embeddings = self._encode(titles)
        desc_embeddings = self._encode(descriptions)

        dates = [
            self._parse_date(a.published_at)
            for a in articles
        ]

        groups = []

        for i, article in enumerate(articles):
            best_group = None
            best_score = 0

            for group in groups:
                if not self._within_date_window(dates[i], group["date"]):
                    continue

                # KURAL 4: Yalnızca kümenin temsilcisi (ilk haber) ile karşılaştır
                rep_index = group["representative_index"]

                title_sim = float(
                    cos_sim(
                        title_embeddings[i],
                        title_embeddings[rep_index]
                    ).item()
                )

                # KURAL 1: Ön Filtre (Fast-fail)
                if title_sim < 0.55:
                    continue

                entity_score = self.entity_detector.similarity(
                    article.title,
                    articles[rep_index].title
                )

                # KURAL 2: Akıllı Entity Filtresi
                if entity_score == 0 and title_sim < 0.80:
                    continue

                # Buraya kadar ulaştıysa Description benzerliğini hesaplamaya değer
                desc_sim = float(
                    cos_sim(
                        desc_embeddings[i],
                        desc_embeddings[rep_index]
                    ).item()
                )

                semantic_score = (
                    self.TITLE_WEIGHT * title_sim
                    +
                    self.DESCRIPTION_WEIGHT * desc_sim
                )
                
                # KURAL 3: Final Skoru
                final_score = semantic_score + (entity_score * 0.08)

                if final_score >= threshold and final_score > best_score:
                    best_score = final_score
                    best_group = group

            if best_group:
                best_group["articles"].append(article)
                # representative_index değişmez, kümenin kurucusu lider kalır

                if dates[i]:
                    if (
                        best_group["date"] is None
                        or dates[i] < best_group["date"]
                    ):
                        best_group["date"] = dates[i]
            else:
                groups.append({
                    "articles": [article],
                    "representative_index": i,  # Kümeyi kuran haber temsilci olur
                    "date": dates[i]
                })

        clusters = []

        for group in groups:
            clusters.append(
                HeadlineCluster(
                    title=self._choose_title(group["articles"]),
                    articles=group["articles"],
                    score=0
                )
            )

        return clusters

    def diagnose_threshold(self, articles, candidate_thresholds=None):
        if candidate_thresholds is None:
            candidate_thresholds = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]

        print(f"[Teşhis] Toplam haber sayısı: {len(articles)}")

        for t in candidate_thresholds:
            clusters = self.remove_duplicates(
                articles,
                threshold=t
            )

            sizes = sorted(
                [len(c.articles) for c in clusters],
                reverse=True
            )

            multi = sum(1 for s in sizes if s > 1)

            print(
                f"threshold={t:.2f} -> "
                f"{len(clusters)} küme "
                f"({multi} tanesi birden fazla haber içeriyor, "
                f"en büyük küme: {sizes[0] if sizes else 0})"
            )

    def inspect_clusters(
        self,
        articles,
        threshold=0.45,
        min_size=3,
        max_clusters_to_show=15
    ):
        clusters = self.remove_duplicates(
            articles,
            threshold=threshold
        )

        big_clusters = [
            c for c in clusters
            if len(c.articles) >= min_size
        ]

        big_clusters.sort(
            key=lambda c: len(c.articles),
            reverse=True
        )

        print(
            f"\n[İnceleme] threshold={threshold:.2f}, "
            f"{min_size}+ haberli "
            f"{len(big_clusters)} küme bulundu "
            f"(ilk {max_clusters_to_show} tanesi gösteriliyor):\n"
        )

        for cluster in big_clusters[:max_clusters_to_show]:
            print(f"--- Küme ({len(cluster.articles)} haber) ---")

            for article in cluster.articles:
                source = getattr(article, "source", "?")
                print(f"  [{source}] {article.title}")

            print()