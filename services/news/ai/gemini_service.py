from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import replace
from typing import Any, Dict, List

from services.news.ai.gemini_client import GeminiClient
from services.news.models.article import Article
from services.news.ranking.headline_cluster import HeadlineCluster


class GeminiService:

    TRANSLATE_CHUNK = 8
    MAX_DESCRIPTION_CHARS = 400

    def __init__(self):
        self.client = GeminiClient()
        # translate ve edit işlemleri için ayrı cache alanları
        self.cache = {'translate': {}, 'edit': {}}

    @staticmethod
    def _hash_value(value: str) -> str:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    @staticmethod
    def _truncate(text: str) -> str:
        if not text:
            return ''
        if len(text) <= GeminiService.MAX_DESCRIPTION_CHARS:
            return text
        return text[:GeminiService.MAX_DESCRIPTION_CHARS].rsplit(' ', 1)[0] + '...'

    @staticmethod
    def _resolve_region(cluster: HeadlineCluster) -> str:
        regions = [
            article.region
            for article in cluster.articles
            if getattr(article, 'region', '')
        ]
        if not regions:
            return 'Global'
        return Counter(regions).most_common(1)[0][0]

    def translate_articles(self, articles: List[Article]) -> List[Article]:
        to_translate = [
            (i, article)
            for i, article in enumerate(articles)
            if getattr(article, 'lang', 'tr').lower() != 'en'
        ]

        if not to_translate:
            return articles

        result = list(articles)
        print(f'[GeminiService] Translating {len(to_translate)} non-English articles')

        for start in range(0, len(to_translate), self.TRANSLATE_CHUNK):
            chunk = to_translate[start:start + self.TRANSLATE_CHUNK]
            prompt = self._build_translate_prompt(chunk)
            
            cache_key = self._hash_value(prompt)
            response = self.cache['translate'].get(cache_key)
            
            if response is None:
                response = self.client.ask(prompt)
                self.cache['translate'][cache_key] = response
                
            translations = self.client.parse_json(response)
            
            if not isinstance(translations, list):
                print('[GeminiService] Unexpected translate response format:', type(translations))
                continue
                
            for item in translations:
                try:
                    index = int(item.get('index'))
                    original_index, article = chunk[index]
                    result[original_index] = replace(
                        article,
                        title=item.get('title', article.title),
                        description=item.get('description', article.description),
                        lang='en'
                    )
                except Exception as exc:
                    print('[GeminiService] translate chunk apply error:', exc)

        return result

    def _build_translate_prompt(self, chunk: List[Any]) -> str:
        items = ''
        for idx, (_, article) in enumerate(chunk):
            items += f"\n{idx})\nTitle:\n{article.title}\n\nDescription:\n{self._truncate(article.description)}\n\n"
        
        return (
            "You are a professional translator."
            "\nTranslate every news title and description into fluent English."
            "\nRules:\n"
            "- Preserve the original meaning.\n"
            "- Preserve names.\n"
            "- Preserve numbers.\n"
            "- Do NOT summarize.\n"
            "- Do NOT explain.\n"
            "- Do NOT omit information.\n"
            "- Return ONLY a valid JSON array.\n"
            "- Do not use markdown.\n"
            "- Do not add extra text.\n"
            "\nJSON format:\n[\n  {\n    \"index\": 0,\n    \"title\": \"...\",\n    \"description\": \"...\"\n  }\n]\n\n"
            f"News:{items}"
        )

    def translate_clusters(self, clusters: List[HeadlineCluster]) -> List[HeadlineCluster]:
        if not clusters:
            return clusters

        items = ""
        for idx, cluster in enumerate(clusters):
            # hasattr veya getattr ile güvenli erişim (opsiyonel ama daha güvenli)
            summary_text = getattr(cluster, 'summary', '') 
            items += (
                f"\n{idx})\n"
                f"Title:\n{cluster.title}\n\n"
                f"Summary:\n{summary_text}\n\n"
            )

        prompt = (
            "You are a professional translator.\n"
            "Translate every news headline and summary into fluent English.\n"
            "Preserve names, numbers and meaning.\n"
            "Do not summarize.\n"
            "Return ONLY valid JSON.\n\n"
            "JSON format:\n"
            "[\n"
            "  {\n"
            '    "index": 0,\n'
            '    "title": "...",\n'
            '    "summary": "..."\n'
            "  }\n"
            "]\n\n"
            f"{items}"
        )

        cache_key = self._hash_value(prompt)
        response = self.cache["translate"].get(cache_key)

        if response is None:
            response = self.client.ask(prompt)
            self.cache["translate"][cache_key] = response

        translations = self.client.parse_json(response)

        if not isinstance(translations, list):
            print("[GeminiService] Unexpected translate format")
            return clusters

        for item in translations:
            try:
                cluster = clusters[int(item["index"])]
                cluster.title = item.get("title", cluster.title)
                cluster.summary = item.get("summary", getattr(cluster, 'summary', ''))
            except Exception as e:
                print("[GeminiService]", e)

        print(f"[GeminiService] Translated {len(clusters)} clusters")
        return clusters

    def edit_news(self, clusters: List[HeadlineCluster]) -> List[Dict[str, Any]]:
        if not clusters:
            return []

        stories = []
        for cluster in clusters:
            stories.append({
                'title': cluster.title,
                'summary': getattr(cluster, 'summary', '') or '',
                'category': getattr(cluster, 'category', '') or '',
                'importance_score': getattr(cluster, 'importance_score', 0),
                'repeat_count': cluster.repeat_count,
                'source_count': cluster.source_count,
                'region': self._resolve_region(cluster),
            })

        prompt = self._build_editor_prompt(stories)
        cache_key = self._hash_value(prompt)
        response = self.cache['edit'].get(cache_key)
        
        if response is None:
            response = self.client.ask(prompt)
            self.cache['edit'][cache_key] = response
            
        result = self.client.parse_json(response)
        
        if not isinstance(result, list):
            print('[GeminiService] Unexpected edit response format:', type(result))
            return []
            
        return result

    def _build_editor_prompt(self, stories: List[Dict[str, Any]]) -> str:
        items = ''
        for idx, story in enumerate(stories):
            items += (
                f"\n{idx})\n"
                f"Title: {story['title']}\n"
                f"Summary: {story['summary']}\n"
                f"Category: {story['category']}\n"
                f"Region: {story['region']}\n"
                f"Importance: {story['importance_score']}\n"
                f"Repeat Count: {story['repeat_count']}\n"
                f"Source Count: {story['source_count']}\n\n"
            )
            
        return (
            "You are a professional news editor.\n"
            "For each story provided, analyze the headline and summary like an editor at a global news agency.\n"
            "Output a JSON array with one object per story.\n"
            "Do not use markdown, do not add any extra text.\n"
            "\nEach item must contain:\n"
            "- title: a polished English headline for the story\n"
            "- summary: a short professional English editor summary\n"
            "- why_it_matters: why this story is important\n"
            "- impact: one of LOW, MEDIUM, HIGH\n"
            "- tags: a list of relevant keywords\n\n"
            f"Input stories:{items}"
        )