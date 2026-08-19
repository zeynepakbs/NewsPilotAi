from pathlib import Path
import subprocess

from paths import get_ffmpeg_path, LATEST_NEWS_VIDEO


class AudioMixer:

    def __init__(self):
        self.ffmpeg = get_ffmpeg_path()
        self.output = LATEST_NEWS_VIDEO

        self.output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.ffmpeg.exists():
            raise FileNotFoundError(
                f"ffmpeg.exe bulunamadı: {self.ffmpeg}"
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
            "-i", str(video),
            "-i", str(audio),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
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