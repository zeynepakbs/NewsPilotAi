from pathlib import Path
import subprocess


class AudioMixer:

    def __init__(self):

        self.root = Path(__file__).resolve().parents[2]

        self.ffmpeg = (
            self.root
            / "tools"
            / "ffmpeg"
            / "ffmpeg.exe"
        )

        self.template = (
            self.root
            / "assets"
            / "videos"
            / "template"
            / "presenter_template.mp4"
        )

        self.output = (
            self.root
            / "assets"
            / "videos"
            / "output"
            / "latest_news.mp4"
        )

        self.output.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    def create_video(
        self,
        audio_file: str
    ):

        audio = Path(audio_file)

        if not self.template.exists():
            raise FileNotFoundError(
                "Template video bulunamadı"
            )

        if not audio.exists():
            raise FileNotFoundError(
                f"Ses bulunamadı: {audio}"
            )


        if self.output.exists():
            self.output.unlink()


        command = [

    str(self.ffmpeg),

    # Template videoyu döngüye al
    "-stream_loop",
    "-1",

    "-i",
    str(self.template),

    # Haber sesi
    "-i",
    str(audio),


    # Video ve ses seçimi

    "-map",
    "0:v:0",

    "-map",
    "1:a:0",


    # Video tekrar kodlanacak

    "-c:v",
    "libx264",

    "-preset",
    "fast",


    # Ses

    "-c:a",
    "aac",

    "-b:a",
    "192k",


    # Ses uzunluğu kadar kes

    "-shortest",


    str(self.output)

]
        subprocess.run(
            command,
            check=True
        )


        return str(self.output)