import json

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

    def _clean_json(self, response: str):
        clean = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(clean)

    def translate_articles(self, articles):
        """
        Sadece 'lang' == 'en' olan haberlerin başlık/açıklamasını
        Türkçeye çevirir. Zaten Türkçe olanlara dokunmaz.
        """

        to_translate = [
            (i, a) for i, a in enumerate(articles) if a.get("lang") != "tr"
        ]

        if not to_translate:
            return articles

        items_text = ""
        for idx, (i, article) in enumerate(to_translate):
            items_text += f"""
{idx}) Başlık: {article["title"]}
Açıklama: {article["description"]}
"""

        prompt = f"""
Sen profesyonel bir haber çevirmenisin.

Aşağıdaki haberlerin başlık ve açıklamalarını doğal, akıcı bir
Türkçeye çevir. Anlamı koru, kelimesi kelimesine çevirme.

SADECE aşağıdaki JSON formatında, aynı sırayla döndür.
Her öğe için "index" alanını değiştirme.

[
  {{"index": 0, "title": "", "description": ""}},
  ...
]

Haberler:
{items_text}
"""

        response = self.ask(prompt)
        translations = self._clean_json(response)

        result = list(articles)
        for t in translations:
            local_idx = t["index"]
            original_i = to_translate[local_idx][0]
            result[original_i] = {
                **result[original_i],
                "title": t.get("title", result[original_i]["title"]),
                "description": t.get("description", result[original_i]["description"]),
            }

        return result

    def analyze_news(self, news_list):

        news_text = ""

        for i, article in enumerate(news_list, start=1):
            news_text += f"""
Haber {i}

Başlık:
{article["title"]}

Açıklama:
{article["description"]}

Kaynak:
{article["source"]}

"""

        prompt = f"""
Sen deneyimli bir uluslararası haber editörüsün.

Aşağıdaki haberler hem Türkiye gündemini hem de dünya gündemini içeriyor.

Görevlerin:

1. Tekrar eden haberleri birleştir.

2. Günün en önemli haberini belirle. Eğer Türkiye ile ilgili
   önemli bir gelişme varsa, onu öncelikli olarak seç; yoksa
   dünya gündeminden en önemli haberi seç.

3. 5-8 adet trend konu çıkar (mümkünse Türkiye ve dünya
   gündemini dengeli şekilde yansıt).

4. Bütün haberleri 4-5 cümlede özetle.

ÖNEMLİ: Tüm çıktı (başlık, alt başlık, kategori, özet, trendler)
KESİNLİKLE Türkçe olmalı.

SADECE aşağıdaki JSON'u döndür.

{{
    "headline": {{
        "title": "",
        "subtitle": "",
        "category": ""
    }},

    "summary": "",

    "trends": []
}}

Haberler:

{news_text}
"""

        response = self.ask(prompt)
        return self._clean_json(response)