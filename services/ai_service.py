from google import genai

from config import GEMINI_API_KEY


class GeminiService:


    def __init__(self):

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )



    def ask(self, prompt: str):

        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        return response.text




    def translate_news(self, news_list):


        texts = "\n\n".join(

            [

                f"""
Haber {i+1}

Kaynak:
{news.get('source', {}).get('name', 'Bilinmiyor')}

Başlık:
{news.get('title', '')}

Açıklama:
{news.get('description', '')}

URL:
{news.get('url', '')}
"""

                for i, news in enumerate(news_list)

            ]

        )



        prompt = f"""

Sen profesyonel bir haber editörüsün.

Aşağıdaki dünya haberlerini Türkçe olarak düzenle.

Kurallar:

- Haber başlığını doğal Türkçe ile yaz.
- Açıklamayı 2-3 cümlelik özet haline getir.
- Haberin anlamını değiştirme.
- Yeni bilgi uydurma.
- Kaynak bilgisini koru.
- Önemli dünya gündemi haberlerini önceliklendir.


Sadece JSON döndür.

Format:

[
 {{
   "title": "Türkçe başlık",
   "description": "Kısa Türkçe özet",
   "source": "Kaynak"
 }}
]


Haberler:

{texts}

"""



        response = self.ask(
            prompt
        )


        clean = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


        return clean