from dataclasses import replace


from services.news.ai.gemini_client import GeminiService

class Translator:

    CHUNK_SIZE = 8
    MAX_DESCRIPTION_CHARS = 400


    def __init__(self):

        self.client = GeminiService()


    def translate_articles(self, articles):

        to_translate = [

            (i, article)

            for i, article in enumerate(articles)

            if article.lang != "en"

        ]


        if not to_translate:

            return articles


        result = list(articles)


        for start in range(

            0,

            len(to_translate),

            self.CHUNK_SIZE

        ):

            chunk = to_translate[

                start:

                start + self.CHUNK_SIZE

            ]


            self._translate_chunk(

                chunk,

                result

            )


        return result



    def _truncate(

        self,

        text

    ):

        if not text:

            return ""


        if len(text) <= self.MAX_DESCRIPTION_CHARS:

            return text


        return (

            text[

                :self.MAX_DESCRIPTION_CHARS

            ]

            .rsplit(

                " ",

                1

            )[0]

            + "..."

        )



    def _translate_chunk(

        self,

        chunk,

        result

    ):


        items = ""


        for idx, (_, article) in enumerate(chunk):

            items += f"""

{idx})

Title:
{article.title}

Description:
{self._truncate(article.description)}

"""



        prompt = f"""

You are a professional translator.

Translate every news title and description into fluent English.

Rules:

- Preserve the original meaning.
- Preserve names.
- Preserve numbers.
- Do NOT summarize.
- Do NOT explain.
- Do NOT omit information.
- Return ONLY a valid JSON array.
- Do not use markdown.
- Do not add extra text.

JSON format:

[
    {{
        "index": 0,
        "title": "...",
        "description": "..."
    }}
]


News:

{items}

"""


        try:

            response = self.client.ask(

                prompt

            )


            translations = self.client.parse_json(

                response

            )


            if isinstance(translations, dict):

                translations = translations.get(

                    "translations",

                    []

                )


            if not isinstance(translations, list):

                print(

                    "[Translator] Beklenmeyen format:",

                    type(translations)

                )

                return



        except Exception as e:

            print(

                "[Translator]",

                e

            )

            return



        for item in translations:


            try:

                local_index = item["index"]


                original_index = chunk[

                    local_index

                ][0]


                article = result[

                    original_index

                ]


                result[

                    original_index

                ] = replace(

                    article,

                    title=item["title"],

                    description=item["description"],

                    lang="en"

                )


            except Exception as e:

                print(

                    "[Translator item error]",

                    e

                )