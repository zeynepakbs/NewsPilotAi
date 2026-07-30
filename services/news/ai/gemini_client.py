import json
import re
import time
import threading

from google import genai
from google.genai import types

from config import GEMINI_API_KEY


class GeminiClient:

    # Ücretsiz katman kotası dakikada 15 istek. Çeviri ve analiz
    # aynı kotayı paylaştığı için güvenli bir pay bırakıyoruz.
    # Bu değerler sınıf seviyesinde: Translator ve NewsAnalyzer
    # ayrı GeminiClient nesneleri oluştursa bile aynı sayaç
    # paylaşılır.
    MAX_REQUESTS_PER_MINUTE = 12
    WINDOW_SECONDS = 60
    MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 5

    _lock = threading.Lock()
    _call_times = []


    def __init__(self):
        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )


    def _wait_for_slot(self):
        """
        Dakikalık istek limitini aşmamak için gerekirse bekler.
        Sınıf seviyesindeki _call_times listesi tüm GeminiClient
        örnekleri arasında paylaşılır.
        """

        while True:

            with GeminiClient._lock:

                now = time.time()

                GeminiClient._call_times = [
                    t for t in GeminiClient._call_times
                    if now - t < self.WINDOW_SECONDS
                ]

                if len(GeminiClient._call_times) < self.MAX_REQUESTS_PER_MINUTE:
                    GeminiClient._call_times.append(now)
                    return

                oldest = GeminiClient._call_times[0]
                wait_time = self.WINDOW_SECONDS - (now - oldest) + 0.5

            if wait_time > 0:
                print(
                    f"[GeminiClient] Dakikalık istek limiti doldu, "
                    f"{wait_time:.1f}s bekleniyor..."
                )
                time.sleep(wait_time)


    @staticmethod
    def _is_quota_error(exc):

        text = str(exc)

        return (
            "RESOURCE_EXHAUSTED" in text
            or "429" in text
        )


    @staticmethod
    def _extract_retry_delay(exc):

        match = re.search(
            r"retryDelay['\"]?\s*:\s*['\"](\d+(?:\.\d+)?)",
            str(exc)
        )

        if match:
            return float(match.group(1)) + 0.5

        return None


    def ask(self, prompt: str):

        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):

            self._wait_for_slot()

            try:

                response = self.client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                        max_output_tokens=8192
                    )
                )

                if not response.candidates:
                    raise RuntimeError(
                        f"Gemini'den candidate dönmedi. "
                        f"Prompt feedback: {getattr(response, 'prompt_feedback', None)}"
                    )

                candidate = response.candidates[0]

                finish_reason = getattr(candidate, "finish_reason", None)

                finish_reason_str = (
                    str(finish_reason).upper()
                    if finish_reason is not None
                    else ""
                )

                if (
                    finish_reason is not None
                    and "STOP" not in finish_reason_str
                    and finish_reason_str != "1"
                ):
                    raise RuntimeError(
                        f"Beklenmeyen finish_reason: {finish_reason}"
                    )

                try:
                    text = response.text

                except Exception as e:
                    raise RuntimeError(
                        "Gemini text özelliğini döndüremedi. "
                        f"Hata: {e}"
                    )

                if not text or not text.strip():
                    raise RuntimeError(
                        "Gemini boş cevap döndürdü."
                    )

                return text


            except Exception as e:

                last_error = e

                if self._is_quota_error(e) and attempt < self.MAX_RETRIES:

                    retry_delay = (
                        self._extract_retry_delay(e)
                        or (self.DEFAULT_RETRY_DELAY * (attempt + 1))
                    )

                    print(
                        f"[GeminiClient] Kota hatası, {retry_delay:.1f}s "
                        f"bekleyip tekrar denenecek "
                        f"(deneme {attempt + 1}/{self.MAX_RETRIES})"
                    )

                    time.sleep(retry_delay)

                    continue

                raise


        raise last_error


    @staticmethod
    def parse_json(response: str):

        if not response or not response.strip():
            raise ValueError("Boş JSON cevabı.")

        clean = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:
            return json.loads(clean)

        except json.JSONDecodeError:

            print(clean[:1000])

            raise