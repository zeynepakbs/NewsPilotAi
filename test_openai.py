from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model="gpt-5-mini",
    input="Sadece şu cümleyi yaz: API bağlantısı başarılı."
)
print(os.getenv("OPENAI_API_KEY")[:10])
print(response.output_text)