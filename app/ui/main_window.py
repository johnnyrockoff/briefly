from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QFrame,
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
        self.setMinimumSize(1100, 740)
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

        # Load first meeting if available
        first_stem = self.meetings_list.get_first_stem()
        if first_stem:
            self.viewer.load_meeting(first_stem)

        # Background dependency & health diagnosis
        QTimer.singleShot(400, self._check_system_health)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)

        # Horizontal Splitter for 2-column layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)

        # ==========================================
        # LEFT PANE: Studio Sidebar
        # ==========================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar_frame")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 6, 12, 6)
        sidebar_layout.setSpacing(12)

        # Brand & Quick Utilities Header
        brand_layout = QHBoxLayout()
        lbl_app_logo = QLabel("🎙️ Briefly")
        lbl_app_logo.setObjectName("lbl_sidebar_title")
        brand_layout.addWidget(lbl_app_logo)
        brand_layout.addStretch()

        self.btn_health = QPushButton("🩺 Health")
        self.btn_health.setToolTip("System dependencies & AI diagnostic check")
        self.btn_health.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_health.clicked.connect(self._open_health_dialog)
        brand_layout.addWidget(self.btn_health)

        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("icon_btn")
        btn_settings.setToolTip("Application Settings")
        btn_settings.setFixedSize(32, 28)
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self._open_settings)
        brand_layout.addWidget(btn_settings)

        sidebar_layout.addLayout(brand_layout)

        # Recording Card (Studio Widget)
        self.record_card = RecordCard()
        sidebar_layout.addWidget(self.record_card)

        # Meetings History List
        self.meetings_list = MeetingsList()
        sidebar_layout.addWidget(self.meetings_list, 1)

        splitter.addWidget(sidebar)

        # ==========================================
        # RIGHT PANE: Main Content Canvas / Viewer
        # ==========================================
        canvas = QWidget()
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(12, 6, 8, 6)
        canvas_layout.setSpacing(10)

        # Health Alert Banner (shown only when a warning/error occurs)
        self.banner_frame = QFrame()
        self.banner_frame.setObjectName("banner_frame")
        self.banner_frame.setStyleSheet(
            "background-color: #312b24; border: 1px solid #fab387; border-radius: 8px; padding: 6px 12px;"
        )
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(4, 2, 4, 2)
        self.lbl_banner = QLabel("")
        self.lbl_banner.setStyleSheet("color: #fab387; font-weight: 600; font-size: 13px;")
        banner_layout.addWidget(self.lbl_banner, 1)

        btn_banner_action = QPushButton("Details / Fix")
        btn_banner_action.setFixedWidth(100)
        btn_banner_action.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_banner_action.clicked.connect(self._open_health_dialog)
        banner_layout.addWidget(btn_banner_action)

        btn_banner_close = QPushButton("✕")
        btn_banner_close.setObjectName("icon_btn")
        btn_banner_close.setFixedSize(28, 28)
        btn_banner_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_banner_close.clicked.connect(self.banner_frame.hide)
        banner_layout.addWidget(btn_banner_close)

        self.banner_frame.hide()
        canvas_layout.addWidget(self.banner_frame)

        # Meeting Viewer
        self.viewer = MeetingViewer()
        canvas_layout.addWidget(self.viewer, 1)

        splitter.addWidget(canvas)

        # Sidebar width ~360px, Canvas takes remainder (~740px)
        splitter.setSizes([360, 740])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter)

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

        # Meetings List & Viewer Selection / Actions
        self.meetings_list.meeting_selected.connect(self.viewer.load_meeting)
        self.meetings_list.transcribe_requested.connect(self._start_transcription)
        self.meetings_list.summarize_requested.connect(self._start_summarization)

        self.viewer.transcribe_requested.connect(self._start_transcription)
        self.viewer.summarize_requested.connect(self._start_summarization)

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
            self.btn_health.setText("🩺 Ready")
            self.btn_health.setStyleSheet("color: #a6da95; font-weight: 600;")
            self.banner_frame.hide()
        elif overall == "warning":
            self.btn_health.setText("▲ Warning")
            self.btn_health.setStyleSheet("color: #fab387; font-weight: 600;")
            warn_items = [it for it in result["items"] if it["status"] == "warning"]
            if warn_items:
                first = warn_items[0]
                self.lbl_banner.setText(f"⚠️ {first['name']}: {first['title']}")
                self.banner_frame.show()
        else:
            self.btn_health.setText("✖ Error")
            self.btn_health.setStyleSheet("color: #ed8796; font-weight: 600;")
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
            self.record_card.refresh_languages()
            self.meetings_list.reload_meetings()
            first = self.meetings_list.get_first_stem()
            if first:
                self.viewer.load_meeting(first)
            else:
                self.viewer.clear()
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
