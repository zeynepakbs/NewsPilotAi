from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QUrl, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from widgets.AvatarWidget import AvatarWidget
from widgets.PlayerControls import PlayerControls


class VideoNewsPlayer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_file = None
        self.video_player = QMediaPlayer(self)
        self.video_widget = QVideoWidget(self)
        self.video_player.setVideoOutput(self.video_widget)

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
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        video_frame = QWidget(self)
        video_frame.setObjectName("videoFrame")
        video_frame.setMouseTracking(True)
        self.video_widget.setMouseTracking(True)

        video_layout = QStackedLayout(video_frame)
        video_layout.setStackingMode(QStackedLayout.StackAll)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        video_layout.addWidget(self.video_widget)

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

        self.controls.setParent(self)
        self.controls.adjustSize()
        self._position_controls()
        self.controls.show()
        self.controls.raise_()

        # keep references for event handling
        self.video_frame = video_frame
        self.avatar_container = avatar_container

        video_frame.installEventFilter(self)
        self.video_widget.installEventFilter(self)
        self.controls.installEventFilter(self)
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
            frame_geom = self.video_frame.geometry()
            x = frame_geom.x() + 20
            y = frame_geom.y() + frame_geom.height() - self.controls.height() - 20
        else:
            x = 20
            y = self.height() - self.controls.height() - 20
        self.controls.move(x, max(0, y))
        self.controls.raise_()

    def set_audio(self, audio_path):
        self.audio_file = str(Path(audio_path).resolve())
        self.audio_player.setSource(QUrl.fromLocalFile(self.audio_file))
        self.audio_player.play()
        self.video_player.play()
        self.show_controls()

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
        super().resizeEvent(event)

    def showEvent(self, event):
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
        self._position_controls()
        self.controls.show()
        self.controls.raise_()
        self.start_controls_timer.start()

    def hide_controls(self):
        self.controls.setVisible(False)
        self.start_controls_timer.stop()