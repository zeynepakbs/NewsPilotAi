from dataclasses import dataclass


@dataclass
class Article:

    title: str
    description: str
    source: str
    url: str
    published_at: str

    lang: str = "tr"
    region: str = ""
    priority: int = 0