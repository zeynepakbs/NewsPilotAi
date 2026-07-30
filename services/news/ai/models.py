from dataclasses import dataclass


@dataclass
class AIAnalysis:
    summary: str
    keywords: list[str]
    importance_reason: str
    category: str