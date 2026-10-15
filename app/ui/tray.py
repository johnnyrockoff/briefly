from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


class SystemTray(QSystemTrayIcon):
    start_recording_requested = Signal()
    stop_recording_requested = Signal()
    toggle_window_requested = Signal()
    open_settings_requested = Signal()
    open_health_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.idle_icon = QIcon(str(RESOURCES_DIR / "tray_idle.svg"))
        self.rec_icon = QIcon(str(RESOURCES_DIR / "tray_recording.svg"))

        self.setIcon(self.idle_icon)
        self.setToolTip("Briefly - AI Meeting Summaries")

        self._is_recording = False
        self._init_menu()

        self.activated.connect(self._on_tray_activated)

    def _init_menu(self):
        self.menu = QMenu()

        self.act_show = QAction("Show Main Window", self.menu)
        self.act_show.triggered.connect(self.toggle_window_requested.emit)
        self.menu.addAction(self.act_show)

        self.menu.addSeparator()

        self.act_record = QAction("▶ Start Recording", self.menu)
        self.act_record.triggered.connect(self._toggle_record_action)
        self.menu.addAction(self.act_record)

        self.menu.addSeparator()

        self.act_health = QAction("🩺 System Health...", self.menu)
        self.act_health.triggered.connect(self.open_health_requested.emit)
        self.menu.addAction(self.act_health)

        self.act_settings = QAction("Settings...", self.menu)
        self.act_settings.triggered.connect(self.open_settings_requested.emit)
        self.menu.addAction(self.act_settings)

        self.menu.addSeparator()

        self.act_quit = QAction("Exit", self.menu)
        self.act_quit.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.act_quit)

        self.setContextMenu(self.menu)

    def set_recording_state(self, is_recording: bool):
        self._is_recording = is_recording
        if is_recording:
            self.setIcon(self.rec_icon)
            self.act_record.setText("⏹ Stop Recording")
            self.setToolTip("Briefly - Recording meeting...")
            self.notify("Recording Started", "Capturing system audio and microphone.")
        else:
            self.setIcon(self.idle_icon)
            self.act_record.setText("▶ Start Recording")
            self.setToolTip("Briefly - AI Meeting Summaries")

    def _toggle_record_action(self):
        if self._is_recording:
            self.stop_recording_requested.emit()
        else:
            self.start_recording_requested.emit()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_window_requested.emit()

    def notify(self, title: str, message: str, icon_type=QSystemTrayIcon.MessageIcon.Information):
        self.showMessage(title, message, icon_type, 4000)
