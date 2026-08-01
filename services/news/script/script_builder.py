from services.news.script.presenter_persona import PresenterPersona


class ScriptBuilder:

    TARGET_DURATION_MINUTES = 8

    def build_prompt(self, clustered_news: list[dict]) -> str:
        """
        clustered_news örneği:

        [
            {
                "title": "...",
                "summary": "...",
                "importance": 97
            },
            ...
        ]
        """

        news_section = []

        for index, news in enumerate(clustered_news, start=1):
            news_section.append(
                f"""
Story {index}
Title: {news['title']}
Summary: {news['summary']}
Importance Score: {news['importance']}
"""
            )

        news_text = "\n".join(news_section)

        return f"""
{PresenterPersona.STYLE}

Below is today's ranked news.

{news_text}

TASK

Write a complete television news broadcast script.

Requirements:

- Speak ONLY in English.
- Begin with a short welcome.
- Present the stories from highest importance to lowest.
- Create smooth transitions.
- Never invent facts.
- Use only the supplied information.
- Avoid repeating information.
- Sound natural and conversational.
- Include occasional subtle humor.
- End with a professional closing.
- The script should be approximately {self.TARGET_DURATION_MINUTES} minutes long.
- Return ONLY the final script.
"""