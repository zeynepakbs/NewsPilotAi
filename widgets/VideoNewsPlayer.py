import re
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, QUrl, QRectF, QSizeF, QThread, Signal, QObject
from PySide6.QtGui import QColor, QFont, QPainter, QTextOption
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QFrame,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem

from widgets.AvatarWidget import AvatarWidget
from widgets.PlayerControls import PlayerControls


def _vtt_time_to_ms(time_str: str) -> int:
    # "00:00:01.234" veya "00:00:01,234" -> milisaniye
    normalized = time_str.replace(",", ".")
    h, m, rest = normalized.split(":")
    s, ms = rest.split(".")
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def _ms_to_srt_time(ms: int) -> str:
    """Milisaniyeyi SRT'nin beklediği 'HH:MM:SS,mmm' formatına çevirir."""
    if ms < 0:
        ms = 0
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write_srt(cues, output_path):
    """Birleştirilmiş (start_ms, end_ms, text) cue listesini standart bir
    .srt dosyasına yazar. Bu, uygulama içinde EKRANDA gösterilen alt
    yazılarla (parse_vtt'nin merged_cues çıktısıyla) birebir aynı
    içeriktedir — ffmpeg'e ham/kelime-kelime .vtt yerine bu dosya
    verildiğinde, indirilen videodaki alt yazı ekrandakiyle eşleşir."""
    lines = []
    for index, (start_ms, end_ms, text) in enumerate(cues, start=1):
        lines.append(str(index))
        lines.append(f"{_ms_to_srt_time(start_ms)} --> {_ms_to_srt_time(end_ms)}")
        lines.append(text)
        lines.append("")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


_TIME_LINE_PATTERN = re.compile(
    r"^(\d{2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[\.,]\d{3})"
)
_INDEX_LINE_PATTERN = re.compile(r"^\d+$")


def parse_vtt(vtt_path: str):
    """
    Satır bazlı, boş satır olsun olmasın çalışan basit bir WebVTT parser.
    Dönüş: [(start_ms, end_ms, text), ...]
    """
    cues = []
    try:
        content = Path(vtt_path).read_text(encoding="utf-8")
    except Exception:
        return cues

    lines = content.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        if not line or line.upper().startswith("WEBVTT") or _INDEX_LINE_PATTERN.match(line):
            i += 1
            continue

        match = _TIME_LINE_PATTERN.match(line)
        if match:
            start_ms = _vtt_time_to_ms(match.group(1))
            end_ms = _vtt_time_to_ms(match.group(2))
            i += 1

            text_lines = []
            while i < n:
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    break
                if _TIME_LINE_PATTERN.match(next_line) or _INDEX_LINE_PATTERN.match(next_line):
                    break
                text_lines.append(next_line)
                i += 1

            text = " ".join(text_lines).strip()
            if text:
                cues.append((start_ms, end_ms, text))
        else:
            i += 1

    if not cues:
        return cues

    merged_cues = [cues[0]]
    for start_ms, end_ms, text in cues[1:]:
        last_start, last_end, last_text = merged_cues[-1]
        gap = start_ms - last_end
        if gap <= 250:
            merged_cues[-1] = (last_start, end_ms, f"{last_text} {text}".strip())
        else:
            merged_cues.append((start_ms, end_ms, text))

    return merged_cues


class _FileCopyWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, source_path, target_path, subtitle_path=None):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path
        self.subtitle_path = subtitle_path

    def _burn_subtitles(self, source: Path, temp_output: Path, subtitle: Path) -> bool:
        """ffmpeg'in subtitles filtresiyle alt yazıyı videonun içine
        gömer (hard-sub / burn-in). ÖNEMLİ: Hedef (nihai) dosyaya değil,
        bir GEÇİCİ dosyaya yazar — böylece ffmpeg yarıda başarısız
        olursa asıl indirilen dosya asla bozuk/yarım kalmaz. Başarılı
        olursa True döner; run() bu durumda temp dosyayı asıl hedefe
        taşır."""
        import subprocess

        if shutil.which("ffmpeg") is None:
            print("[DEBUG] ffmpeg PATH'te bulunamadı, subtitle burn atlanıyor.")
            return False

        # ffmpeg'in subtitles filtresi Windows path'lerindeki ':' ve '\'
        # karakterlerini özel biçimde bekler. Path'i forward-slash'e
        # çevirip ':' karakterini kaçırıyoruz (örn. "C:/x" -> "C\:/x").
        sub_filter_path = str(subtitle).replace("\\", "/").replace(":", r"\:")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(source),
            "-vf", f"subtitles='{sub_filter_path}'",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(temp_output),
        ]
        print(f"[DEBUG] ffmpeg komutu: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        if result.returncode != 0:
            # DEBUG: ffmpeg neden başarısız oldu, tam olarak görelim.
            print(f"[DEBUG] ffmpeg returncode={result.returncode}")
            print(f"[DEBUG] ffmpeg stderr:\n{result.stderr}")
            return False

        # Dosya gerçekten oluşmuş ve boş değilse (0 byte değilse) başarılı
        # sayıyoruz. returncode==0 tek başına yeterli güvence değil; bazı
        # durumlarda ffmpeg 0 dönüp de anlamsız/boş bir dosya bırakabilir.
        if not temp_output.exists() or temp_output.stat().st_size == 0:
            print(f"[DEBUG] ffmpeg returncode 0 ama çıktı dosyası yok/boş: {temp_output}")
            return False

        return True

    def run(self):
        try:
            source = Path(self.source_path)
            target = Path(self.target_path)
            if not source.exists():
                self.error.emit("The source video file was not found.")
                return
            target.parent.mkdir(parents=True, exist_ok=True)

            subtitle = Path(self.subtitle_path) if self.subtitle_path else None
            # DEBUG: alt yazı gömme adımının neden/nasıl çalıştığını
            # (ya da çalışmadığını) görmek için eklendi.
            print(f"[DEBUG] subtitle_path={self.subtitle_path}, subtitle_exists={subtitle.exists() if subtitle else False}, ffmpeg_found={shutil.which('ffmpeg') is not None}")

            if subtitle and subtitle.exists():
                # ffmpeg çıktısını ASIL hedefe değil, aynı klasördeki
                # geçici bir dosyaya yazıyoruz. Böylece ffmpeg başarısız
                # olsa bile target dosyası hiçbir zaman yarım/bozuk
                # kalmaz — ya tamamen geçerli bir dosya olur ya da hiç
                # dokunulmamış (fallback kopya) olur.
                temp_output = target.with_name(f"_tmp_{target.name}")
                if temp_output.exists():
                    temp_output.unlink()

                burned = False
                try:
                    burned = self._burn_subtitles(source, temp_output, subtitle)
                except Exception as burn_exc:
                    print(f"[DEBUG] _burn_subtitles exception: {burn_exc}")
                    burned = False

                print(f"[DEBUG] burned={burned}")

                if burned:
                    # Geçici dosya geçerli: asıl hedefin üzerine taşı.
                    if target.exists():
                        target.unlink()
                    shutil.move(str(temp_output), str(target))
                else:
                    # ffmpeg başarısız oldu: geçici dosyayı temizle ve
                    # kullanıcı en azından videosuz-altyazı halini
                    # alsın diye düz kopyaya düş.
                    if temp_output.exists():
                        temp_output.unlink()
                    shutil.copy2(source, target)
            else:
                shutil.copy2(source, target)

            self.finished.emit(str(target))
        except Exception as exc:
            self.error.emit(str(exc))


class VideoNewsPlayer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_file = None
        self.subtitle_cues = []

        self.video_player = QMediaPlayer(self)
        self.scene = QGraphicsScene(self)
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        self.video_player.setVideoOutput(self.video_item)

        self.audio_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.controls = PlayerControls(self)

        # controls connections
        self.controls.download_button.clicked.connect(self.download_current_video)

        self.video_player.mediaStatusChanged.connect(self.on_video_status_changed)
        self.audio_player.mediaStatusChanged.connect(self.on_audio_status_changed)
        self.audio_player.positionChanged.connect(self.on_audio_position_changed)

        # create a single-shot timer for hiding controls on inactivity
        # (Eğer eklenecekse buraya QTimer eklenebilir)

        self.current_video_path = None
        self.current_subtitle_path = None
        self.download_worker = None
        self.download_thread = None
        self.audio_ready = False
        self.video_ready = False
        self.playback_started = False
        self.pending_audio_path = None
        self.pending_subtitle_path = None

        self.setup_ui()
        self.load_video()
        # allow keyboard focus to receive key events
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def setup_ui(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("videoPage")
        self.setStyleSheet(
            """
            QWidget#videoPage {
                background-color: #050608;
            }

            QWidget#videoFrame {
                border-radius: 20px;
                background-color: #0d111a;
            }

            QWidget#playerControlsOverlay {
                background-color: rgba(0, 0, 0, 0.48);
                border-radius: 14px;
            }

            QPushButton#playerControlButton {
                background-color: rgba(255, 255, 255, 0.14);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#playerControlButton:hover {
                background-color: rgba(255, 255, 255, 0.26);
            }

            QLabel#subtitleLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
                background-color: rgba(0, 0, 0, 0.55);
                border-radius: 8px;
                padding: 6px 14px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        video_frame = QWidget(self)
        video_frame.setObjectName("videoFrame")
        video_frame.setMouseTracking(True)

        self.view = QGraphicsView(self.scene, video_frame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setRenderHints(self.view.renderHints() | QPainter.Antialiasing)

        video_layout = QStackedLayout(video_frame)
        video_layout.setStackingMode(QStackedLayout.StackAll)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        video_layout.addWidget(self.view)

        avatar = AvatarWidget(self)
        avatar.setFixedSize(300, 320)
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.addStretch()
        avatar_layout.addWidget(avatar, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        avatar_layout.addSpacing(18)

        avatar_container = QWidget(self)
        avatar_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        avatar_container.setLayout(avatar_layout)
        avatar_container.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(avatar_container)

        # ÖNEMLİ: Ara "overlay" widget'ı tamamen kaldırıldı.
        # Önceki denemelerde overlay (transparan ya da değil) ile
        # controls arasındaki ekstra parent katmanı, fare tıklamalarının
        # butona ulaşmasını engelleyen belirsiz bir davranışa yol
        # açıyordu. Şimdi controls, video_frame'in DOĞRUDAN çocuğu —
        # aradaki katman kalktı, tıklama olayı doğrudan controls'a
        # (ve içindeki download_button'a) gidiyor.
        self.controls.setParent(video_frame)
        self.controls.adjustSize()
        self.controls.show()
        self.controls.raise_()

        self.subtitle_item = QGraphicsTextItem("")
        self.subtitle_item.setDefaultTextColor(Qt.white)
        self.subtitle_item.setFont(QFont("Arial", 16, QFont.DemiBold))
        self.subtitle_item.document().setDefaultTextOption(QTextOption(Qt.AlignCenter))
        self.subtitle_item.setZValue(2)
        self.subtitle_item.setTextWidth(0)
        self.subtitle_item.setVisible(False)
        self.scene.addItem(self.subtitle_item)

        self.subtitle_bg = QGraphicsRectItem()
        self.subtitle_bg.setBrush(QColor(0, 0, 0, 160))
        self.subtitle_bg.setPen(Qt.NoPen)
        self.subtitle_bg.setZValue(1)
        self.subtitle_bg.setVisible(False)
        self.scene.addItem(self.subtitle_bg)

        # keep references for event handling
        self.video_frame = video_frame
        self.avatar_container = avatar_container

        video_frame.installEventFilter(self)
        self.controls.installEventFilter(self)
        avatar_container.installEventFilter(self)

        layout.addWidget(video_frame, stretch=1)

        # NOT: Burada artık _position_controls() ÇAĞRILMIYOR.
        # setup_ui() aşamasında video_frame henüz gerçek boyutuna
        # ulaşmamış olduğu için (height=0 olabilir), buton yanlış
        # bir konumda (örn. ekranın en üstünde, avatar'ın arkasında)
        # hesaplanıp orada takılı kalabiliyordu. Gerçek boyutlar ancak
        # showEvent / resizeEvent tetiklendiğinde belli olduğundan,
        # pozisyonlama o noktalarda yapılıyor (aşağıya bakın).

    def load_video(self):
        video_path = Path("assets/videos/template/presenter_template.mp4").resolve()
        self.video_player.setSource(QUrl.fromLocalFile(str(video_path)))
        self.video_ready = True
        self._start_playback_if_ready()
        self.show_controls()

    def download_current_video(self):
        # DEBUG: Bu satır, tıklamanın gerçekten butona ulaşıp
        # ulaşmadığını konsoldan görmek için eklendi. Sorun çözülünce
        # kaldırabilirsiniz.
        print(f"[DEBUG] download_current_video tetiklendi. current_video_path={self.current_video_path}, enabled={self.controls.download_button.isEnabled()}")

        if not self.current_video_path or not Path(self.current_video_path).exists():
            QMessageBox.warning(self, "Download failed", "No final video is available yet.")
            return

        default_name = Path(self.current_video_path).name if self.current_video_path else "daily_news.mp4"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save video",
            default_name,
            "MP4 Video Files (*.mp4)"
        )
        if not save_path:
            return

        if not save_path.lower().endswith(".mp4"):
            save_path = f"{save_path}.mp4"

        self._start_download_copy(self.current_video_path, save_path, self._prepare_burn_subtitle_path())

    def _prepare_burn_subtitle_path(self):
        """İndirilen videoya gömülecek alt yazı dosyasını hazırlar.
        Ham .vtt yerine, ekranda gösterilenle BİREBİR AYNI (kelime
        kelime değil, birleştirilmiş cümleler halinde) bir .srt dosyası
        üretir. self.subtitle_cues zaten _prepare_subtitles() içinde
        parse_vtt() ile birleştirilmiş halde saklanıyor."""
        if not self.subtitle_cues:
            # Birleştirilmiş cue yoksa (örn. alt yazı hiç yüklenmediyse)
            # elimizdeki ham .vtt'ye geri düşüyoruz.
            return self.current_subtitle_path

        try:
            srt_path = Path(self.current_video_path).with_name("_burn_subtitles.srt")
            write_srt(self.subtitle_cues, srt_path)
            return str(srt_path)
        except Exception as exc:
            print(f"[DEBUG] Birleştirilmiş .srt oluşturulamadı, ham .vtt kullanılacak: {exc}")
            return self.current_subtitle_path

    def _start_download_copy(self, source_path, target_path, subtitle_path=None):
        self.download_thread = QThread(self)
        self.download_worker = _FileCopyWorker(source_path, target_path, subtitle_path)
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.error.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_worker.error.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def _on_download_finished(self, target_path):
        QMessageBox.information(self, "Download complete", f"Video saved to:\n{target_path}")

    def _on_download_error(self, message):
        QMessageBox.critical(self, "Download failed", message)

    def set_current_video_path(self, video_path):
        """
        Final video dosyası hazır olduğunda pipeline tarafından bu metod
        çağrılmalı. Bu çağrı yapılmadan download_button hiçbir zaman
        enabled duruma geçmez ve pasif (soluk) görünmeye devam eder.
        Örnek kullanım (pipeline'ın video üretimini bitirdiği yerde):
            self.video_news_player.set_current_video_path(final_video_path)
        """
        self.current_video_path = video_path
        exists = bool(video_path and Path(video_path).exists())
        # DEBUG: set_current_video_path gerçekten çağrılıyor mu ve
        # path diskte var mı, bunu görmek için eklendi.
        print(f"[DEBUG] set_current_video_path çağrıldı. video_path={video_path}, exists={exists}")
        self.controls.download_button.setEnabled(exists)

    def _position_controls(self):
        if not hasattr(self, "video_frame"):
            return

        frame_height = self.video_frame.height()
        frame_width = self.video_frame.width()

        # video_frame henüz layout tarafından boyutlandırılmadıysa
        # (örn. widget henüz gösterilmediyse) hesaplama yapmıyoruz;
        # aksi halde buton negatif/0 pozisyonda "kaybolabiliyordu".
        if frame_height <= 0 or frame_width <= 0:
            return

        self.controls.adjustSize()
        x = 20
        y = frame_height - self.controls.height() - 20
        self.controls.move(x, max(0, y))
        self.controls.raise_()

        if hasattr(self, "subtitle_item"):
            text_width = min(900, max(180, frame_width - 80))
            self.subtitle_item.setTextWidth(text_width)
            rect = self.subtitle_item.boundingRect()
            sx = (frame_width - rect.width()) / 2
            sy = frame_height - self.controls.height() - rect.height() - 28
            self.subtitle_item.setPos(sx, max(0, sy))
            self.subtitle_bg.setRect(rect.adjusted(-14, -10, 14, 10))
            self.subtitle_bg.setPos(self.subtitle_item.pos())

    def set_audio(self, audio_path, subtitle_path=None):
        self.pending_audio_path = str(Path(audio_path).resolve())
        self.pending_subtitle_path = subtitle_path
        self.audio_file = self.pending_audio_path
        # İndirme sırasında alt yazıyı videoya gömebilmek için yolu
        # sınıf düzeyinde de saklıyoruz.
        self.current_subtitle_path = (
            str(Path(subtitle_path).resolve()) if subtitle_path else None
        )
        self.audio_player.setSource(QUrl.fromLocalFile(self.audio_file))
        self.audio_ready = True
        self._prepare_subtitles(subtitle_path)
        self._start_playback_if_ready()
        self.show_controls()

    def _prepare_subtitles(self, subtitle_path=None):
        self.subtitle_cues = []
        self.subtitle_item.setPlainText("")
        self.subtitle_item.setVisible(False)
        self.subtitle_bg.setVisible(False)

        if subtitle_path and Path(subtitle_path).exists():
            self.subtitle_cues = parse_vtt(str(subtitle_path))
            if self.subtitle_cues:
                self.subtitle_item.setVisible(True)
                self.subtitle_bg.setVisible(True)

    def _start_playback_if_ready(self):
        if self.playback_started:
            return
        if not self.video_ready or not self.audio_ready:
            return
        self.playback_started = True
        self.audio_player.play()
        self.video_player.play()
        self.show_controls()

    def on_audio_position_changed(self, position_ms):
        if not self.subtitle_cues:
            return

        current_text = ""
        for start_ms, end_ms, text in self.subtitle_cues:
            if start_ms <= position_ms <= end_ms:
                current_text = text
                break

        if self.subtitle_item.toPlainText() != current_text:
            self.subtitle_item.setPlainText(current_text)
            self.subtitle_item.setVisible(bool(current_text))
            self.subtitle_bg.setVisible(bool(current_text))
            self._position_controls()

    def play_media(self):
        if self.audio_file:
            self.audio_player.play()
        self.video_player.play()
        self.show_controls()

    def pause_media(self):
        self.audio_player.pause()
        self.show_controls()

    def on_video_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.video_player.setPosition(0)
            if self.audio_player.playbackState() == QMediaPlayer.PlayingState:
                self.video_player.play()

    def on_audio_status_changed(self, status):
        return

    def stop_media(self):
        self.audio_player.stop()
        self.show_controls()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def _raise_controls(self):
        """controls'u video_frame'in diğer tüm alt widget'larının
        (view, avatar_container) EN ÜSTÜNE çıkarır. overlay ara katmanı
        kaldırıldığı için artık doğrudan controls üzerinde çalışıyor."""
        if hasattr(self, "controls"):
            self.controls.raise_()

    def resizeEvent(self, event):
        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.resize(self.video_frame.size())
            self.view.setSceneRect(QRectF(0, 0, self.video_frame.width(), self.video_frame.height()))
            self.video_item.setSize(QSizeF(self.video_frame.width(), self.video_frame.height()))
        self._raise_controls()
        self._position_controls()
        super().resizeEvent(event)

    def showEvent(self, event):
        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.resize(self.video_frame.size())
            self.view.setSceneRect(QRectF(0, 0, self.video_frame.width(), self.video_frame.height()))
            self.video_item.setSize(QSizeF(self.video_frame.width(), self.video_frame.height()))
        self._raise_controls()
        self._position_controls()
        super().showEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        # Space: toggle audio play/pause (audio only)
        if key == Qt.Key_Space:
            from PySide6.QtMultimedia import QMediaPlayer as _QMP
            state = self.audio_player.playbackState()
            if state == _QMP.PlayingState:
                self.pause_media()
            else:
                self.play_media()
            return

        # Right arrow: seek forward 5s
        if key == Qt.Key_Right:
            pos = self.audio_player.position()
            duration = self.audio_player.duration()
            new = pos + 5000
            if duration > 0:
                new = min(new, duration)
            self.audio_player.setPosition(new)
            return

        # Left arrow: seek backward 5s
        if key == Qt.Key_Left:
            pos = self.audio_player.position()
            new = max(pos - 5000, 0)
            self.audio_player.setPosition(new)
            return

        # Up arrow: increase volume by 10%
        if key == Qt.Key_Up:
            vol = self.audio_output.volume()
            vol = min(vol + 0.1, 1.0)
            self.audio_output.setVolume(vol)
            return

        # Down arrow: decrease volume by 10%
        if key == Qt.Key_Down:
            vol = self.audio_output.volume()
            vol = max(vol - 0.1, 0.0)
            self.audio_output.setVolume(vol)
            return

        return super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        self.show_controls()
        super().mouseMoveEvent(event)

    def show_controls(self):
        self._raise_controls()
        self._position_controls()
        self.controls.show()
        self.controls.raise_()

    def hide_controls(self):
        self.controls.hide()