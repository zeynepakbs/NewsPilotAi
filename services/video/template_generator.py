from pathlib import Path
import subprocess


class TemplateGenerator:

    def __init__(self):

        self.root = Path(__file__).resolve().parents[2]

        self.ffmpeg = (
            self.root
            / "tools"
            / "ffmpeg"
            / "ffmpeg.exe"
        )

        self.image = (
            self.root
            / "assets"
            / "presenter_scene.png"
        )

        self.output = (
            self.root
            / "assets"
            / "videos"
            / "template"
            / "presenter_template.mp4"
        )

        self.output.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    def create(self):
        if self.output.exists():
            return str(self.output)

        command = [

            str(self.ffmpeg),

            "-loop",
            "1",

            "-i",
            str(self.image),

            "-vf",

            ("zoompan="
             "z='1.0+0.05*sin(on/50)':"
             "x='iw/2-(iw/zoom/2)':"
             "y='ih/2-(ih/zoom/2)':"
             "d=1:"
            "s=1920x1080"
            ),
            "-t",
             "20",

            "-c:v",
            "libx264",

            "-pix_fmt",
            "yuv420p",
            

            str(self.output)

        ]


        subprocess.run(
            command,
            check=True
        )


        return str(self.output)