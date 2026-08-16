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
        video_file: str,
        audio_file: str,
    ):

        video = Path(video_file)
        audio = Path(audio_file)

        if not video.exists():
            raise FileNotFoundError(
                f"Scrolling video bulunamadı: {video}"
            )

        if not audio.exists():
            raise FileNotFoundError(
                f"Ses bulunamadı: {audio}"
            )

        if self.output.exists():
            self.output.unlink()

        command = [

            str(self.ffmpeg),

            "-y",

            "-i",
            str(video),

            "-i",
            str(audio),

            "-map",
            "0:v:0",

            "-map",
            "1:a:0",

            "-c:v",
            "libx264",

            "-preset",
            "fast",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-shortest",

            str(self.output),

        ]

        subprocess.run(
            command,
            check=True,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0
            ),
        )

        return str(self.output)
