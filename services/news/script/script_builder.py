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

Write a complete news podcast script.

Requirements:

- Speak ONLY in natural English.
- Write 1000–1200 words (approximately {self.TARGET_DURATION_MINUTES} minutes).
- Sound like a charismatic podcast host rather than a stiff formal TV anchor.
- Address the audience naturally (e.g., "Welcome back everyone", "Let's jump into our first story").
- Present the stories from highest importance to lowest.
- Use smooth transitions such as "Meanwhile...", "On a different note...", "Speaking of...", "Here's something interesting...".
- Use light reactions like "(smiles)" or "(laughs softly)" only when appropriate.
- NEVER joke about deaths, disasters, wars, crimes or other sensitive topics.
- Keep the information accurate and use only the supplied stories. Never invent facts.
- Avoid repeating facts.
- Use short spoken sentences suitable for automatic English subtitles.
- Use natural B2–C1 English: fluent, conversational, and human-like.
- Do not sound as simple as B1 or as unnecessarily advanced as C2.
- Finish with a warm closing inviting viewers back tomorrow.
- Return ONLY the final script (no Markdown, no JSON, no notes).
"""