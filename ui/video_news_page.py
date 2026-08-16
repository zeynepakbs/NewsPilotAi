from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from widgets.VideoNewsPlayer import VideoNewsPlayer
from workers.news_worker import NewsWorker


class VideoNewsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.video_player_widget = VideoNewsPlayer(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video oynatıcının tüm pencereyi tam olarak kaplamasını sağlıyoruz
        layout.addWidget(self.video_player_widget)

        # Sayfanın arka planını koyu stüdyo temasına sabitliyoruz
        self.setStyleSheet("background-color: #0b0f19;")

        self.thread = None
        self.worker = None

        self.start_worker()

    def start_worker(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(3000)

        self.thread = QThread(self)
        self.worker = NewsWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_finished(self, result):
        video_path = result.get("video")
        if video_path:
            self.video_player_widget.set_video(video_path)

    def on_error(self, message):
        print("NewsWorker error:", message)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(3000)
        super().closeEvent(event)