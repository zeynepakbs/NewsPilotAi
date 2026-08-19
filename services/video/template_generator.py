from pathlib import Path
import subprocess

from paths import get_ffmpeg_path, PRESENTER_SCENE_PNG, PRESENTER_TEMPLATE_MP4


# DEPRECATED: Eski presenter/zoompan pipeline. Aktif akış
# services/video/scrolling_text_generator.py kullanır.
class TemplateGenerator:

    def __init__(self):
        self.ffmpeg = get_ffmpeg_path()
        self.image = PRESENTER_SCENE_PNG
        self.output = PRESENTER_TEMPLATE_MP4

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