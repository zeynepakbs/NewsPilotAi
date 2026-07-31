from services.news.models.article import Article


class RegionDetector:

    REGION_MAP = {
        'tr': 'Turkey',
        'us': 'USA',
        'eu': 'Europe',
        'as': 'Asia',
    }

    def detect(self, source_region: str, article: Article) -> str:
        if source_region in self.REGION_MAP:
            return self.REGION_MAP[source_region]

        source_name = getattr(article, 'source', '') or ''
        lower_source = source_name.lower()

        if 'middle east' in lower_source or 'gulf' in lower_source:
            return 'Middle East'

        return 'Global'
