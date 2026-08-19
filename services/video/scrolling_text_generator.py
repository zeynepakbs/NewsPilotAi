from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from paths import (
    WIN_FONTS_DIR,
    TEMPLATE_VIDEOS_DIR,
    SCROLLING_TEXT_STRIP_PNG,
    SCROLLING_TEXT_VIDEO_MP4,
    get_ffmpeg_path,
    get_ffprobe_path,
)



class ScrollingTextGenerator:
    """
    Script metninden sessiz, dikey kayan video üretir.

    Özellikler:
    - 1920x1080
    - 25 FPS
    - Metin videonun ilk karesinde görünür.
    - Gereksiz üst siyah boşluk yoktur.
    - Metin yukarı doğru akar.
    - Haber sırası yukarıdan aşağıya doğrudur.
    - Video süresi TTS ses süresine eşitlenir.
    """

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 25

    # Arka plan
    BG_COLOR = (13, 17, 23)

    # Yazı
    TEXT_COLOR = (230, 237, 243)

    # Kenar boşlukları
    MARGIN_X = 120
    MARGIN_TOP = 100
    MARGIN_BOTTOM = 100

    # Paragraf ve satır aralıkları
    PARAGRAPH_GAP = 50
    LINE_GAP = 18

    # Font boyutları
    BODY_FONT_SIZE = 34
    HEADLINE_FONT_SIZE = 42
    BRAND_FONT_SIZE = 28

    # Ses çok kısa olursa minimum video süresi
    MIN_DURATION = 5.0

    def __init__(self):
        self.ffmpeg = get_ffmpeg_path()
        self.ffprobe = get_ffprobe_path()
        self.temp_dir = TEMPLATE_VIDEOS_DIR

        self.temp_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.text_strip_path = SCROLLING_TEXT_STRIP_PNG
        self.video_output = SCROLLING_TEXT_VIDEO_MP4

        # Eski dosyaları temizle
        if self.text_strip_path.exists():
            try:
                self.text_strip_path.unlink()
            except PermissionError:
                pass

        if self.video_output.exists():
            try:
                self.video_output.unlink()
            except PermissionError:
                pass


    # ============================================================
    # PUBLIC
    # ============================================================

    def create(
        self,
        script: str,
        audio_file: str,
    ) -> str:

        script = (script or "").strip()

        if not script:
            raise ValueError(
                "Scrolling text video için script boş olamaz."
            )

        audio_path = Path(audio_file)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Ses dosyası bulunamadı: {audio_path}"
            )

        # --------------------------------------------------------
        # 1. Ses süresini al
        # --------------------------------------------------------

        duration = self._get_audio_duration(
            audio_path
        )

        duration = max(
            duration,
            self.MIN_DURATION,
        )

        print(
            f"[ScrollingText] Ses süresi: "
            f"{duration:.3f} saniye"
        )

        # --------------------------------------------------------
        # 2. Metin PNG'sini oluştur
        # --------------------------------------------------------

        self._render_text_strip(script)

        # --------------------------------------------------------
        # 3. PNG boyutunu yazdır
        # --------------------------------------------------------

        with Image.open(
            self.text_strip_path
        ) as image:

            print(
                f"[ScrollingText] PNG boyutu: "
                f"{image.width}x{image.height}"
            )

        # --------------------------------------------------------
        # 4. Video oluştur
        # --------------------------------------------------------

        self._encode_scrolling_video(
            duration
        )

        print(
            f"[ScrollingText] Video oluşturuldu: "
            f"{self.video_output}"
        )

        # --------------------------------------------------------
        # 5. ÇIKTIYI DOĞRULA
        #
        # Video dosyası gerçekten diskte var mı ve boş değil mi?
        # Sessizce "video yok ama hata da yok" durumunu engeller.
        # --------------------------------------------------------

        if not self.video_output.exists():
            raise RuntimeError(
                "FFmpeg hata vermeden bitti ama çıktı dosyası "
                f"oluşmadı: {self.video_output}"
            )

        size_mb = (
            self.video_output.stat().st_size
            / (1024 * 1024)
        )

        print(
            f"[ScrollingText] Video boyutu: "
            f"{size_mb:.2f} MB"
        )

        if size_mb <= 0:
            raise RuntimeError(
                "Video dosyası oluştu ama 0 byte. "
                "FFmpeg encode sırasında sessizce başarısız oldu."
            )

        return str(self.video_output)

    # ============================================================
    # BINARY
    # ============================================================

    def _resolve_binary(
        self,
        bundled: Path,
        fallback_name: str,
    ) -> str:

        if bundled.exists():
            return str(bundled)

        found = shutil.which(
            fallback_name
        )

        if found:
            return found

        raise FileNotFoundError(
            f"{fallback_name} bulunamadı. "
            f"Beklenen konum: {bundled}"
        )

    # ============================================================
    # AUDIO DURATION
    # ============================================================

    def _get_audio_duration(
        self,
        audio_path: Path,
    ) -> float:

        ffprobe = self._resolve_binary(
            self.ffprobe,
            "ffprobe",
        )

        command = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default="
            "noprint_wrappers=1:"
            "nokey=1",
            str(audio_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if hasattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                )
                else 0
            ),
        )

        output = result.stdout.strip()

        if not output:
            raise RuntimeError(
                "FFprobe ses süresini okuyamadı."
            )

        return float(output)

    # ============================================================
    # FONT
    # ============================================================

    def _load_font(
        self,
        size: int,
        bold: bool = False,
    ):

        candidates = []

        if bold:
            candidates.extend(
                [
                    WIN_FONTS_DIR / "segoeuib.ttf",
                    WIN_FONTS_DIR / "arialbd.ttf",
                ]
            )

        candidates.extend(
            [
                WIN_FONTS_DIR / "segoeui.ttf",
                WIN_FONTS_DIR / "arial.ttf",
            ]
        )


        for candidate in candidates:

            if candidate.exists():

                return ImageFont.truetype(
                    str(candidate),
                    size,
                )

        return ImageFont.load_default()

    # ============================================================
    # TEXT WRAPPING
    # ============================================================

    def _wrap_paragraph(
        self,
        text: str,
        font,
        max_width: int,
        draw: ImageDraw.ImageDraw,
    ) -> list[str]:

        words = text.split()

        if not words:
            return []

        lines = []

        current = words[0]

        for word in words[1:]:

            candidate = (
                f"{current} {word}"
            )

            width = draw.textlength(
                candidate,
                font=font,
            )

            if width <= max_width:

                current = candidate

            else:

                lines.append(
                    current
                )

                current = word

        lines.append(current)

        return lines

    # ============================================================
    # PARAGRAPH SPLIT
    # ============================================================

    def _split_paragraphs(
        self,
        script: str,
    ) -> list[str]:

        normalized = (
            script
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .strip()
        )

        parts = re.split(
            r"\n\s*\n",
            normalized,
        )

        paragraphs = [
            part.strip()
            for part in parts
            if part.strip()
        ]

        if paragraphs:
            return paragraphs

        return [normalized]

    # ============================================================
    # TEXT STRIP
    # ============================================================

    def _render_text_strip(
        self,
        script: str,
    ) -> None:

        body_font = self._load_font(
            self.BODY_FONT_SIZE
        )

        headline_font = self._load_font(
            self.HEADLINE_FONT_SIZE,
            bold=True,
        )

        brand_font = self._load_font(
            self.BRAND_FONT_SIZE,
            bold=True,
        )

        max_width = (
            self.WIDTH
            - (2 * self.MARGIN_X)
        )

        # --------------------------------------------------------
        # Ölçüm için küçük canvas
        # --------------------------------------------------------

        probe = Image.new(
            "RGB",
            (self.WIDTH, 100),
            self.BG_COLOR,
        )

        probe_draw = ImageDraw.Draw(
            probe
        )

        # --------------------------------------------------------
        # Layout
        # --------------------------------------------------------

        layout_blocks = []

        # Marka
        layout_blocks.append(
            (
                brand_font,
                [
                    "NewsPilot AI",
                    "Daily News Briefing",
                ],
            )
        )

        # Marka ile ilk haber arasında boşluk
        layout_blocks.append(
            (
                body_font,
                [""],
            )
        )

        # --------------------------------------------------------
        # Haberleri işle
        # --------------------------------------------------------

        paragraphs = (
            self._split_paragraphs(
                script
            )
        )

        for paragraph in paragraphs:

            # İlk cümleyi başlık gibi göster
            sentences = re.split(
                r"(?<=[.!?])\s+",
                paragraph,
            )

            first_sentence = (
                sentences[0].strip()
                if sentences
                else paragraph
            )

            remainder = " ".join(
                s.strip()
                for s in sentences[1:]
                if s.strip()
            )

            # ----------------------------------------------------
            # Başlık
            # ----------------------------------------------------

            if first_sentence:

                headline_lines = (
                    self._wrap_paragraph(
                        first_sentence,
                        headline_font,
                        max_width,
                        probe_draw,
                    )
                )

                layout_blocks.append(
                    (
                        headline_font,
                        headline_lines,
                    )
                )

            # ----------------------------------------------------
            # Haber gövdesi
            # ----------------------------------------------------

            if remainder:

                body_lines = (
                    self._wrap_paragraph(
                        remainder,
                        body_font,
                        max_width,
                        probe_draw,
                    )
                )

                layout_blocks.append(
                    (
                        body_font,
                        body_lines,
                    )
                )

            # ----------------------------------------------------
            # Haberler arasında boşluk
            # ----------------------------------------------------

            layout_blocks.append(
                (
                    body_font,
                    [""],
                )
            )

        # ========================================================
        # TOPLAM METİN YÜKSEKLİĞİ
        # ========================================================

        total_text_height = 0

        for font, lines in layout_blocks:

            for line in lines:

                if not line:

                    total_text_height += (
                        self.PARAGRAPH_GAP
                    )

                    continue

                total_text_height += (
                    font.size
                    + self.LINE_GAP
                )

        image_height = (
            self.MARGIN_TOP
            + total_text_height
            + self.MARGIN_BOTTOM
        )

        # Video yüksekliğinden küçük olamaz
        image_height = max(
            image_height,
            self.HEIGHT,
        )

        # FFmpeg için güvenli çift sayı
        if image_height % 2 != 0:
            image_height += 1

        # ========================================================
        # IMAGE
        # ========================================================

        image = Image.new(
            "RGB",
            (
                self.WIDTH,
                image_height,
            ),
            self.BG_COLOR,
        )

        draw = ImageDraw.Draw(
            image
        )

        y = self.MARGIN_TOP

        for font, lines in layout_blocks:

            for line in lines:

                if not line:

                    y += self.PARAGRAPH_GAP

                    continue

                draw.text(
                    (
                        self.MARGIN_X,
                        y,
                    ),
                    line,
                    font=font,
                    fill=self.TEXT_COLOR,
                )

                y += (
                    font.size
                    + self.LINE_GAP
                )

        # ========================================================
        # PNG KAYDET
        # ========================================================

        image.save(
            self.text_strip_path,
            format="PNG",
            optimize=True,
        )

        print(
            "[ScrollingText] PNG oluşturuldu: "
            f"{self.text_strip_path}"
        )

    # ============================================================
    # VIDEO
    # ============================================================

    def _encode_scrolling_video(
        self,
        duration: float,
    ) -> None:

        ffmpeg = self._resolve_binary(
            self.ffmpeg,
            "ffmpeg",
        )

        # --------------------------------------------------------
        # PNG yüksekliği
        # --------------------------------------------------------

        with Image.open(
            self.text_strip_path
        ) as image:

            text_height = image.height

        # --------------------------------------------------------
        # Kaydırma mesafesi
        # --------------------------------------------------------

        travel_distance = max(
            text_height - self.HEIGHT,
            0,
        )

        actual_duration = max(
            duration,
            self.MIN_DURATION,
        )

        if travel_distance <= 0:

            speed = 0.0

        else:

            speed = (
                travel_distance
                / actual_duration
            )

        print(
            f"[ScrollingText] Strip: "
            f"{self.WIDTH}x{text_height}"
        )

        print(
            f"[ScrollingText] "
            f"Kaydırma mesafesi: "
            f"{travel_distance}px"
        )

        print(
            f"[ScrollingText] "
            f"Video süresi: "
            f"{actual_duration:.3f}s"
        )

        print(
            f"[ScrollingText] "
            f"Kaydırma hızı: "
            f"{speed:.6f}px/s"
        )

        # ========================================================
        # FFmpeg FILTER
        # ========================================================

        if travel_distance > 0:

            # ----------------------------------------------------
            # KRİTİK DÜZELTME:
            #
            # Önceki sürüm "<=" ve ">" gibi infix karşılaştırma
            # operatörleri kullanıyordu. FFmpeg'in eval motoru
            # (libavutil/eval.c) bu operatörleri infix biçimde
            # DESTEKLEMEZ — sadece lt()/gt()/lte()/gte()/min()/max()
            # gibi FONKSİYONLAR geçerlidir. Bu yüzden ifade parse
            # edilemiyordu ve ffmpeg şu hatayı veriyordu:
            #
            #   Missing ')' in '(...<=3506)+3506*(...>3506))'
            #
            # Doğru ve çok daha basit çözüm: min().
            #
            # min() FFmpeg eval'de virgülle ayrılmış iki argüman
            # alır. Ama "-vf" içinde "crop=...,format=..." şeklinde
            # filtreleri virgülle ayırdığımız için, min() içindeki
            # virgülün filtre ayırıcısıyla karışmaması için "\,"
            # ile kaçırılması ZORUNLUDUR.
            #
            # crop, x/y ifadelerini zaten her karede otomatik
            # olarak yeniden hesaplar (eval diye bir parametreye
            # gerek yok, o sadece zoompan/drawtext gibi filtrelerde
            # var).
            # ========================================================

            y_expression = (
                f"trunc(min({speed:.6f}*t\\,{travel_distance}))"
            )

            video_filter = (
                f"crop="
                f"{self.WIDTH}:"
                f"{self.HEIGHT}:"
                f"0:"
                f"{y_expression},"
                f"format=yuv420p"
            )

        else:

            video_filter = (
                "scale="
                f"{self.WIDTH}:"
                f"{self.HEIGHT},"
                "format=yuv420p"
            )

        print(
            "[ScrollingText] FFmpeg filter:"
        )

        print(
            f"  {video_filter}"
        )

        # --------------------------------------------------------
        # Eski video
        # --------------------------------------------------------

        if self.video_output.exists():

            try:
                self.video_output.unlink()

            except PermissionError as exc:

                raise RuntimeError(
                    "Eski scrolling_text_video.mp4 "
                    "dosyası kullanımda. "
                    "Video oynatıcısını kapatıp "
                    "tekrar deneyin."
                ) from exc

        # ========================================================
        # FFMPEG COMMAND
        # ========================================================

        command = [
            ffmpeg,

            "-y",

            "-loop",
            "1",

            "-i",
            str(
                self.text_strip_path
            ),

            "-vf",
            video_filter,

            "-t",
            f"{actual_duration:.3f}",

            "-r",
            str(self.FPS),

            "-c:v",
            "libx264",

            "-preset",
            "ultrafast",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-an",

            str(
                self.video_output
            ),
        ]

        print(
            "[ScrollingText] "
            "FFmpeg başlıyor..."
        )

        print(
            "[ScrollingText] Komut: "
            + " ".join(command)
        )

        # ========================================================
        # RUN
        # ========================================================

        try:

            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,

                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                    )
                    else 0
                ),
            )

            if result.stdout:
                print(
                    result.stdout
                )

            if result.stderr:
                print(
                    "[FFmpeg]"
                )

                print(
                    result.stderr
                )

        except subprocess.CalledProcessError as exc:

            print(
                "[ScrollingText] "
                "FFmpeg HATASI:"
            )

            if exc.stdout:
                print(
                    exc.stdout
                )

            if exc.stderr:
                print(
                    exc.stderr
                )

            raise