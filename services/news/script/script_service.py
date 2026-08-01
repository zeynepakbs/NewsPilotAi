from services.news.ai.gemini_client import GeminiClient
from services.news.script.script_builder import ScriptBuilder


class ScriptService:

    def __init__(self):
        self.client = GeminiClient()
        self.builder = ScriptBuilder()

    def generate(self, clustered_news: list[dict]) -> str:
        """
        Generates an approximately 8-minute news broadcast script.

        Parameters
        ----------
        clustered_news : list[dict]
            [
                {
                    "title": "...",
                    "summary": "...",
                    "importance": 97
                },
                ...
            ]

        Returns
        -------
        str
            Final presenter script.
        """

        prompt = self.builder.build_prompt(clustered_news)

        response = self.client.generate(prompt)

        return response.strip()