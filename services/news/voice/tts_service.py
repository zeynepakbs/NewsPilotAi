import edge_tts
import asyncio
import os
from paths import OUTPUTS_DIR



class TTSService:

    def __init__(self):
        self.voice = "en-US-GuyNeural"

    @staticmethod
    def _srt_to_vtt(srt_text: str) -> str:
        """SRT formatındaki altyazıyı WebVTT formatına çevirir."""
        vtt_body = srt_text.replace(",", ".")
        return "WEBVTT\n\n" + vtt_body

    async def _generate(
        self,
        text,
        output
    ):
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            boundary="WordBoundary"
        )

        # Altyazı oluşturucu
        submaker = edge_tts.SubMaker()

        # Altyazı dosyasının yolu (mp3 ile aynı klasörde, .vtt uzantılı)
        sub_path = output.replace(".mp3", ".vtt")

        # Hem sesi diske yazıyoruz hem de zaman damgalarını submaker'a veriyoruz
        with open(output, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # SRT üretip VTT formatına çeviriyoruz
        srt_content = submaker.get_srt()
        vtt_content = self._srt_to_vtt(srt_content)

        with open(sub_path, "w", encoding="utf-8") as sub_file:
            sub_file.write(vtt_content)

        # İki dosyayı da döndürüyoruz
        return output, sub_path

    def generate(
        self,
        text,
        filename="daily_news.mp3"
    ):

        print("[TTS] başladı")
        print("[TTS] karakter sayısı:", len(text))

        OUTPUTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        output = str(OUTPUTS_DIR / filename)

        audio_path, subtitle_path = asyncio.run(
            self._generate(
                text,
                output
            )
        )


        if os.path.exists(audio_path):
            size = os.path.getsize(audio_path) / 1024
            print(
                f"[TTS] Ses oluşturuldu: {audio_path} ({size:.2f} KB)"
            )
            print(
                f"[TTS] Altyazı oluşturuldu: {subtitle_path}"
            )
        else:
            print(
                "[TTS] HATA: dosya oluşmadı"
            )

        return audio_path, subtitle_path