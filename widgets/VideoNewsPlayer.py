from pathlib import Path
import shutil

from PySide6.QtCore import Qt, QUrl, QRectF, QSizeF, QThread, Signal, QObject
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QGraphicsView,
    QGraphicsScene,
    QFrame,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem

from widgets.PlayerControls import PlayerControls


class _FileCopyWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, source_path, target_path):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path

    def run(self):
        try:
            source = Path(self.source_path)
            target = Path(self.target_path)
            if not source.exists():
                self.error.emit("The source video file was not found.")
                return

            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            self.finished.emit(str(target))
        except Exception as exc:
            self.error.emit(str(exc))


class VideoNewsPlayer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_video_path = None
        self.download_worker = None
        self.download_thread = None

        self.video_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.video_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.GlobalColor.black)
        
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        self.video_player.setVideoOutput(self.video_item)

        self.controls = PlayerControls(self)
        self.controls.download_button.clicked.connect(self.download_current_video)

        self.setup_ui()
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

            QGraphicsView {
                background-color: #0d111a;
                border: none;
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

        self.controls.setParent(video_frame)
        self.controls.adjustSize()
        self.controls.show()
        self.controls.raise_()

        self.video_frame = video_frame
        self.video_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        video_frame.installEventFilter(self)
        self.controls.installEventFilter(self)

        layout.addWidget(video_frame)

    def set_video(self, video_path):
        if not video_path:
            return

        resolved = str(Path(video_path).resolve())
        self.current_video_path = resolved
        exists = Path(resolved).exists()
        self.controls.download_button.setEnabled(exists)

        if not exists:
            return

        self.video_player.setSource(QUrl.fromLocalFile(resolved))
        self.video_player.play()
        self.show_controls()

    def set_current_video_path(self, video_path):
        self.set_video(video_path)

    def download_current_video(self):
        if not self.current_video_path or not Path(self.current_video_path).exists():
            QMessageBox.warning(self, "Download failed", "No final video is available yet.")
            return

        default_name = Path(self.current_video_path).name
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save video",
            default_name,
            "MP4 Video Files (*.mp4)",
        )
        if not save_path:
            return

        if not save_path.lower().endswith(".mp4"):
            save_path = f"{save_path}.mp4"

        self._start_download_copy(self.current_video_path, save_path)

    def _start_download_copy(self, source_path, target_path):
        self.download_thread = QThread(self)
        self.download_worker = _FileCopyWorker(source_path, target_path)
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

    def _position_controls(self):
        if not hasattr(self, "video_frame"):
            return

        frame_height = self.video_frame.height()
        frame_width = self.video_frame.width()

        if frame_height <= 0 or frame_width <= 0:
            return

        self.controls.adjustSize()
        x = 20
        y = frame_height - self.controls.height() - 20
        self.controls.move(x, max(0, y))
        self.controls.raise_()

    def play_media(self):
        self.video_player.play()
        self.show_controls()

    def pause_media(self):
        self.video_player.pause()
        self.show_controls()

    def stop_media(self):
        self.video_player.stop()
        self.show_controls()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def _raise_controls(self):
        if hasattr(self, "controls"):
            self.controls.raise_()

    def resizeEvent(self, event):
        self._update_video_frame_size()

        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.setGeometry(self.video_frame.rect())

            self.view.setSceneRect(
                QRectF(
                    0,
                    0,
                    self.video_frame.width(),
                    self.video_frame.height(),
                )
            )

            self.video_item.setSize(
                QSizeF(
                    self.video_frame.width(),
                    self.video_frame.height(),
                )
            )

        self._raise_controls()
        self._position_controls()

        super().resizeEvent(event)

    def showEvent(self, event):
        self._update_video_frame_size()

        if hasattr(self, "view") and hasattr(self, "video_frame"):
            self.view.setGeometry(self.video_frame.rect())

            self.view.setSceneRect(
                QRectF(
                    0,
                    0,
                    self.video_frame.width(),
                    self.video_frame.height(),
                )
            )

            self.video_item.setSize(
                QSizeF(
                    self.video_frame.width(),
                    self.video_frame.height(),
                )
            )

        self._raise_controls()
        self._position_controls()

        super().showEvent(event)

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

    def _update_video_frame_size(self):
        if not hasattr(self, "video_frame"):
            return

        parent_width = self.width()

        if parent_width <= 0:
            return

        
        video_height = int(parent_width * 9 / 16)

        
        video_height = min(
            video_height,
            self.height() - 32,
        )

        if video_height <= 0:
            return

        self.video_frame.setFixedHeight(video_height)