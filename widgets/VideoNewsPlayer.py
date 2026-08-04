import re
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QUrl, QTimer, QRectF, QSizeF
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
        self.controls.play_button.clicked.connect(self.toggle_play)
        self.controls.volume_slider.valueChanged.connect(self.set_volume)
        self.controls.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        self.video_player.mediaStatusChanged.connect(self.on_video_status_changed)
        self.audio_player.mediaStatusChanged.connect(self.on_audio_status_changed)
        self.audio_player.positionChanged.connect(self.on_audio_position_changed)

        # create a single-shot timer for hiding controls on inactivity
        self.start_controls_timer = QTimer(self)
        self.start_controls_timer.setSingleShot(True)
        self.start_controls_timer.setInterval(3000)
        self.start_controls_timer.timeout.connect(self.hide_controls)

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

        overlay = QWidget(video_frame)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay.setAttribute(Qt.WA_StyledBackground)
        overlay.setStyleSheet("background: transparent;")
        video_layout.addWidget(overlay)

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

        self.controls.setParent(overlay)
        self.controls.adjustSize()
        self._position_controls()
        self.controls.show()
        self.controls.raise_()

        # keep references for event handling
        self.overlay = overlay

        # keep references for event handling
        self.video_frame = video_frame
        self.avatar_container = avatar_container

        video_frame.installEventFilter(self)
        self.controls.installEventFilter(self)
        overlay.installEventFilter(self)
        avatar_container.installEventFilter(self)

        layout.addWidget(video_frame, stretch=1)

    def load_video(self):
        video_path = Path("assets/videos/template/presenter_template.mp4").resolve()
        self.video_player.setSource(QUrl.fromLocalFile(str(video_path)))
        self.video_player.play()
        self.show_controls()

    def _position_controls(self):
        self.controls.adjustSize()
        if hasattr(self, "video_frame"):
            frame_height = self.video_frame.height()
            frame_width = self.video_frame.width()
            x = 20
            y = frame_height - self.controls.height() - 20
        else:
            x = 20
            y = self.height() - self.controls.height() - 20
        self.controls.move(x, max(0, y))
        self.controls.raise_()

        if hasattr(self, "subtitle_item") and hasattr(self, "video_frame"):
            frame_height = self.video_frame.height()
            frame_width = self.video_frame.width()
            text_width = min(900, max(180, frame_width - 80))
            self.subtitle_item.setTextWidth(text_width)
            rect = self.subtitle_item.boundingRect()
            sx = (frame_width - rect.width()) / 2
            sy = frame_height - self.controls.height() - rect.height() - 28
            self.subtitle_item.setPos(sx, max(0, sy))
            self.subtitle_bg.setRect(rect.adjusted(-14, -10, 14, 10))
            self.subtitle_bg.setPos(self.subtitle_item.pos())

    def set_audio(self, audio_path, subtitle_path=None):
        self.audio_file = str(Path(audio_path).resolve())
        self.audio_player.setSource(QUrl.fromLocalFile(self.audio_file))
        self.audio_player.play()
        self.video_player.play()

        self.subtitle_cues = []
        self.subtitle_item.setPlainText("")
        self.subtitle_item.setVisible(False)
        self.subtitle_bg.setVisible(False)

        if subtitle_path and Path(subtitle_path).exists():
            self.subtitle_cues = parse_vtt(str(subtitle_path))
            if self.subtitle_cues:
                self.subtitle_item.setVisible(True)
                self.subtitle_bg.setVisible(True)

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
            print(f"[SUBTITLE] position_ms={position_ms} text={current_text}")
            self.subtitle_item.setPlainText(current_text)
            self.subtitle_item.setVisible(bool(current_text))
            self.subtitle_bg.setVisible(bool(current_text))
            self._position_controls()

    def play_media(self):
        # play audio (if any); always keep video playing
        if self.audio_file:
            self.audio_player.play()
            self.controls.play_button.setText("❚❚")
        self.video_player.play()
        self.show_controls()

    def pause_media(self):
        # pause audio only; keep presenter video running
        self.audio_player.pause()
        self.controls.play_button.setText("▶")
        self.show_controls()

    def toggle_play(self):
        # toggle audio play/pause; keep video always playing
        state = self.audio_player.playbackState()
        from PySide6.QtMultimedia import QMediaPlayer as _QMP
        if state == _QMP.PlayingState:
            self.pause_media()
        else:
            self.play_media()

    def toggle_fullscreen(self):
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()

    def on_video_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.video_player.setPosition(0)
            self.video_player.play()

    def on_audio_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.controls.play_button.setText("▶")

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def stop_media(self):
        self.audio_player.stop()
        self.controls.play_button.setText("▶")
        self.show_controls()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.Enter):
            self.show_controls()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        self._position_controls()
        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.resize(self.video_frame.size())
            self.view.setSceneRect(QRectF(0, 0, self.video_frame.width(), self.video_frame.height()))
            self.video_item.setSize(QSizeF(self.video_frame.width(), self.video_frame.height()))
        if hasattr(self, "overlay") and hasattr(self, "video_frame"):
            self.overlay.resize(self.video_frame.size())
        super().resizeEvent(event)

    def showEvent(self, event):
        self._position_controls()
        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.resize(self.video_frame.size())
            self.view.setSceneRect(QRectF(0, 0, self.video_frame.width(), self.video_frame.height()))
            self.video_item.setSize(QSizeF(self.video_frame.width(), self.video_frame.height()))
        if hasattr(self, "overlay") and hasattr(self, "video_frame"):
            self.overlay.resize(self.video_frame.size())
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
        self._position_controls()
        self.controls.show()
        self.controls.raise_()
        self.start_controls_timer.start()

    def hide_controls(self):
        self.controls.setVisible(False)
        self.start_controls_timer.stop()