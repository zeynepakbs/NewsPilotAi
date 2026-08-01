import edge_tts
import asyncio
import os


class TTSService:

    def __init__(self):
        self.voice = "en-US-GuyNeural"


    async def _generate(
        self,
        text,
        output
    ):

        communicate = edge_tts.Communicate(
            text,
            self.voice
        )

        await communicate.save(
            output
        )


    def generate(
        self,
        text,
        filename="headless_voice.mp3"
    ):

        print("[TTS] başladı")
        print("[TTS] karakter sayısı:", len(text))

        os.makedirs(
            "outputs",
            exist_ok=True
        )

        output = os.path.join(
            "outputs",
            filename
        )

        asyncio.run(
            self._generate(
                text,
                output
            )
        )

        if os.path.exists(output):
            size = os.path.getsize(output) / 1024

            print(
                f"[TTS] Ses oluşturuldu: {output} ({size:.2f} KB)"
            )

        else:
            print(
                "[TTS] HATA: dosya oluşmadı"
            )

        return output