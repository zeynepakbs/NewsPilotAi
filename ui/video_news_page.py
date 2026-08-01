from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from workers.news_worker import NewsWorker


class VideoNewsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.thread = None
        self.worker = None
        
        self.audio_file = None
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(
            self.audio_output
        )
        self.audio_output.setVolume(
            80
        )

        self.setup_ui()
        self.start_worker()

    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            40,
            30,
            40,
            30
        )

        layout.setSpacing(
            20
        )

        self.title = QLabel(
            "🤵 Headless White Collar"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )

        font = self.title.font()
        font.setPointSize(18)
        font.setBold(True)

        self.title.setFont(
            font
        )

        layout.addWidget(
            self.title
        )

        self.status = QLabel(
            "Preparing the agenda..."
        )

        self.status.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.status
        )

        self.play_button = QPushButton(
            "▶ Listen to the News"
        )
        self.play_button.setEnabled(
            False
        )
        self.play_button.clicked.connect(
            self.play_audio
        )
        layout.addWidget(
            self.play_button
        )

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.text_area = QLabel(
            ""
        )
        
        self.text_area.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        self.text_area.setWordWrap(
            True
        )

        self.scroll.setWidget(
            self.text_area
        )

        layout.addWidget(
            self.scroll
        )


    def start_worker(self):

        self.thread = QThread(
            self
        )

        self.worker = NewsWorker()

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.finished.connect(
            self.show_result
        )

        self.worker.error.connect(
            self.show_error
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.error.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )
        
        self.thread.finished.connect(
            self.on_thread_finished
        )

        self.thread.start()


    def on_thread_finished(self):
        
        self.worker = None
        self.thread = None


    def show_result(self, result):

        self.status.setText(
            "Agenda is ready"
        )

        script = result.get(
            "script",
            "Script not found"
        )

        self.text_area.setText(
            script
        )

        audio = result.get(
            "audio"
        )

        if audio:
            self.audio_file = audio

            self.player.setSource(
                QUrl.fromLocalFile(
                    audio
                )
            )

            self.play_button.setEnabled(
                True
            )


    def show_error(self, message):

        self.status.setText(
            "An error occurred"
        )

        self.text_area.setText(
            str(message)
        )


    def play_audio(self):
        if self.audio_file:
            self.player.play()


    def closeEvent(self, event):

        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(
                3000
            )

        event.accept()