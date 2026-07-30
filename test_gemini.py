from services.news.ai.ai_service import GeminiService

gemini = GeminiService()

response = gemini.ask("Merhaba, bana kendini tanıt.")

print(response)