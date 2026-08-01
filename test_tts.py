from services.news.voice.tts_service import TTSService


text = """
Good evening.
I am the Headless White-Collar.
Welcome to today's global news briefing.
"""


tts = TTSService()

tts.generate(
    text
)