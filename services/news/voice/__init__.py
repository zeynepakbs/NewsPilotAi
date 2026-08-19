import edge_tts
import asyncio
import os
from paths import OUTPUTS_DIR


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

        OUTPUTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        output = str(OUTPUTS_DIR / filename)


        asyncio.run(
            self._generate(
                text,
                output
            )
        )



        print(
            f"[TTS] Ses oluşturuldu: {output}"
        )


        return output