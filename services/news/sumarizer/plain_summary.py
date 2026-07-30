import re


def build_plain_summary(cluster, max_sentences=3):
    """
    Gemini'ye hiç istek atmadan, cluster içindeki makalelerin
    (zaten çevrilmiş) description alanından 2-3 cümlelik
    başlıksız düz yazı üretir. Kota tüketmez.
    """

    candidates = [
        article
        for article in cluster.articles
        if getattr(article, "description", "")
    ]

    if candidates:

        representative = max(
            candidates,
            key=lambda a: len(a.description)
        )

        text = representative.description

    else:

        text = getattr(cluster, "summary", "") or getattr(cluster, "title", "")

    if not text:
        return ""

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text.strip()
    )

    sentences = [
        s.strip()
        for s in sentences
        if s.strip()
    ]

    return " ".join(sentences[:max_sentences])