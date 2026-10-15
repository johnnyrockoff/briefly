from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.audio.recorder import AudioRecorder
from app.config import RECORDINGS_DIR, SUMMARIES_DIR, TRANSCRIPTS_DIR, config
from app.health import run_full_system_check
from app.summarization.summarizer import SummarizerManager
from app.transcription.transcriber import TranscriberManager
from app.ui.components.health_dialog import HealthCheckDialog
from app.ui.components.meetings_list import MeetingsList
from app.ui.components.record_card import RecordCard
from app.ui.components.settings_dialog import SettingsDialog
from app.ui.components.viewer import MeetingViewer
from app.ui.tray import SystemTray

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Briefly - Intelligent Meeting Summaries")
        self.setMinimumSize(1050, 720)
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "icon.svg")))

        # Backend Managers
        self.recorder = AudioRecorder(self)
        self.transcriber = TranscriberManager(self)
        self.summarizer = SummarizerManager(self)

        # Tray
        self.tray = SystemTray(self)
        self.tray.show()

        self._init_ui()
        self._connect_signals()

        # Carregar primeira reunião da lista se houver
        if self.meetings_list.table.rowCount() > 0:
            first_item = self.meetings_list.table.item(0, 0)
            if first_item:
                stem = first_item.data(Qt.ItemDataRole.UserRole)
                if stem:
                    self.viewer.load_meeting(stem)

        # Diagnóstico de dependências em segundo plano após inicialização
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, self._check_system_health)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # Header Superior
        header_layout = QHBoxLayout()

        lbl_app_logo = QLabel("🎙️ Briefly")
        lbl_app_logo.setStyleSheet("font-size: 19px; font-weight: bold; color: #89b4fa;")
        header_layout.addWidget(lbl_app_logo)

        lbl_app_subtitle = QLabel("• Local Automation with Whisper & Ollama")
        lbl_app_subtitle.setStyleSheet("font-size: 13px; color: #a6adc8; margin-top: 4px;")
        header_layout.addWidget(lbl_app_subtitle)

        header_layout.addStretch()

        self.btn_health = QPushButton("🩺 System Check")
        self.btn_health.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_health.clicked.connect(self._open_health_dialog)
        header_layout.addWidget(self.btn_health)

        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self._open_settings)
        header_layout.addWidget(btn_settings)

        main_layout.addLayout(header_layout)

        # Health Alert Banner (hidden by default)
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet(
            "background-color: #312b24; border: 1px solid #fab387; border-radius: 8px; padding: 6px 12px;"
        )
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(4, 2, 4, 2)
        self.lbl_banner = QLabel("")
        self.lbl_banner.setStyleSheet("color: #fab387; font-weight: 500;")
        banner_layout.addWidget(self.lbl_banner, 1)

        btn_banner_action = QPushButton("Details / Fix")
        btn_banner_action.setFixedWidth(100)
        btn_banner_action.clicked.connect(self._open_health_dialog)
        banner_layout.addWidget(btn_banner_action)

        btn_banner_close = QPushButton("✕")
        btn_banner_close.setFixedWidth(30)
        btn_banner_close.clicked.connect(self.banner_frame.hide)
        banner_layout.addWidget(btn_banner_close)

        self.banner_frame.hide()
        main_layout.addWidget(self.banner_frame)

        # Card de Gravação (Início / Parada rápida e dispositivos)
        self.record_card = RecordCard()
        main_layout.addWidget(self.record_card)

        # Splitter Principal (Histórico à Esquerda | Visualizador à Direita)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Lado Esquerdo: Lista de Reuniões
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.meetings_list = MeetingsList()
        left_layout.addWidget(self.meetings_list)
        splitter.addWidget(left_container)

        # Lado Direito: Visualizador de Resumo
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = MeetingViewer()
        right_layout.addWidget(self.viewer)
        splitter.addWidget(right_container)

        # Proporção inicial: 42% lista, 58% visualizador
        splitter.setSizes([450, 600])
        main_layout.addWidget(splitter, 1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to record meetings.")

    def _connect_signals(self):
        # Record Card -> Recorder
        self.record_card.start_requested.connect(self._start_recording)
        self.record_card.stop_requested.connect(self._stop_recording)

        # Recorder -> UI & Tray
        self.recorder.state_changed.connect(self.record_card.set_recording_state)
        self.recorder.state_changed.connect(self.tray.set_recording_state)
        self.recorder.tick.connect(self.record_card.update_timer)
        self.recorder.finished.connect(self._on_recording_finished)
        self.recorder.error.connect(self._on_error)

        # Tray -> Actions
        self.tray.start_recording_requested.connect(self._start_recording)
        self.tray.stop_recording_requested.connect(self._stop_recording)
        self.tray.toggle_window_requested.connect(self._toggle_window)
        self.tray.open_settings_requested.connect(self._open_settings)
        self.tray.open_health_requested.connect(self._open_health_dialog)
        self.tray.quit_requested.connect(self._quit_application)

        # Meetings List -> Viewer / Pipelines
        self.meetings_list.meeting_selected.connect(self.viewer.load_meeting)
        self.meetings_list.transcribe_requested.connect(self._start_transcription)
        self.meetings_list.summarize_requested.connect(self._start_summarization)

        # Transcriber -> UI & Tray
        self.transcriber.progress.connect(lambda msg: self.viewer.set_processing_status(msg, True))
        self.transcriber.progress.connect(self.status_bar.showMessage)
        self.transcriber.finished.connect(self._on_transcription_finished)
        self.transcriber.error.connect(self._on_transcription_error)

        # Summarizer -> UI & Tray
        self.summarizer.progress.connect(lambda msg: self.viewer.set_processing_status(msg, True))
        self.summarizer.progress.connect(self.status_bar.showMessage)
        self.summarizer.finished.connect(self._on_summarization_finished)
        self.summarizer.error.connect(self._on_summarization_error)

    # --- Recording Handlers ---
    def _start_recording(self):
        success = self.recorder.start_recording()
        if success:
            self.status_bar.showMessage("Audio recording in progress...")

    def _stop_recording(self):
        self.status_bar.showMessage("Stopping recording and finalizing audio file...")
        self.recorder.stop_recording()

    def _on_recording_finished(self, wav_path: str):
        self.status_bar.showMessage(f"Audio recorded: {Path(wav_path).name}")
        self.tray.notify("Recording Finished", f"File saved: {Path(wav_path).name}")
        self.meetings_list.reload_meetings()
        stem = Path(wav_path).stem
        self.viewer.load_meeting(stem)

        # Automação: Transcrever automaticamente se configurado
        if config.get("auto_transcribe", True):
            self._start_transcription(wav_path)

    # --- Transcription Handlers ---
    def _start_transcription(self, wav_path: str):
        stem = Path(wav_path).stem
        self.viewer.load_meeting(stem)
        self.viewer.set_processing_status(f"Starting transcription of {stem}...", True)
        self.transcriber.start_transcription(wav_path)

    def _on_transcription_finished(self, wav_path: str, txt_path: str):
        stem = Path(txt_path).stem
        self.status_bar.showMessage(f"Transcription finished: {stem}")
        self.tray.notify("Transcription Completed", f"Transcription of {stem} was saved successfully.")
        self.meetings_list.reload_meetings()
        self.viewer.load_meeting(stem)
        self.viewer.set_processing_status("Transcription completed successfully.", False)

        # Automação: Resumir automaticamente se configurado
        if config.get("auto_summarize", True):
            self._start_summarization(txt_path)

    def _on_transcription_error(self, err_msg: str):
        self.status_bar.showMessage(f"Transcription error: {err_msg}")
        self.viewer.hide_processing_status()
        QMessageBox.critical(self, "Transcription Error", err_msg)

    # --- Summarization Handlers ---
    def _start_summarization(self, txt_path: str):
        stem = Path(txt_path).stem
        self.viewer.load_meeting(stem)
        self.viewer.set_processing_status(f"Generating summary for {stem} with local AI...", True)
        self.summarizer.start_summarization(txt_path)

    def _on_summarization_finished(self, txt_path: str, md_path: str, content: str):
        stem = Path(md_path).stem
        self.status_bar.showMessage(f"Summary completed: {stem}")
        self.tray.notify("Summary Ready!", f"Summary for meeting {stem} was generated and saved.")
        self.meetings_list.reload_meetings()
        self.viewer.load_meeting(stem)
        self.viewer.set_processing_status("Summary completed successfully!", False)

    def _on_summarization_error(self, err_msg: str):
        self.status_bar.showMessage(f"Error generating summary: {err_msg}")
        self.viewer.hide_processing_status()
        QMessageBox.critical(self, "AI Summary Error", err_msg)

    def _on_error(self, err_msg: str):
        self.status_bar.showMessage(f"Error: {err_msg}")
        QMessageBox.warning(self, "Warning", err_msg)

    # --- Window & Tray State ---
    def _check_system_health(self):
        result = run_full_system_check()
        overall = result["overall"]

        if overall == "ok":
            self.btn_health.setText("🩺 System Ready")
            self.btn_health.setStyleSheet("color: #a6e3a1;")
            self.banner_frame.hide()
        elif overall == "warning":
            self.btn_health.setText("▲ System Warning")
            self.btn_health.setStyleSheet("color: #fab387;")
            # Procura item com warning
            warn_items = [it for it in result["items"] if it["status"] == "warning"]
            if warn_items:
                first = warn_items[0]
                self.lbl_banner.setText(f"⚠️ {first['name']}: {first['title']}")
                self.banner_frame.show()
        else:
            self.btn_health.setText("✖ System Error")
            self.btn_health.setStyleSheet("color: #f38ba8;")
            err_items = [it for it in result["items"] if it["status"] == "error"]
            if err_items:
                first = err_items[0]
                self.lbl_banner.setText(f"❌ {first['name']}: {first['title']}")
                self.banner_frame.show()

    def _open_health_dialog(self):
        dlg = HealthCheckDialog(self)
        dlg.exec()
        self._check_system_health()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.record_card.refresh_devices()
            self.status_bar.showMessage("Settings updated.")
            self._check_system_health()

    def _toggle_window(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def _quit_application(self):
        if self.recorder.is_recording:
            reply = QMessageBox.question(
                self,
                "Recording in Progress",
                "A recording is currently in progress. Are you sure you want to stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.recorder.stop_recording()
            else:
                return

        self.tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        if config.get("minimize_to_tray_on_close", True):
            event.ignore()
            self.hide()
            self.tray.notify(
                "Briefly Minimized",
                "Briefly continues running in the system tray for quick recordings."
            )
        else:
            self._quit_application()
            event.accept()
