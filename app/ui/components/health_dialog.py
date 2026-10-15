import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.hardware import detect_system_hardware
from app.health import run_full_system_check
from app.installer import DependencyInstaller


class HealthCheckDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Health & AI Dependency Manager")
        self.resize(680, 580)
        self.installer = DependencyInstaller(self)
        self.installer.progress.connect(self._on_install_progress)
        self.installer.finished.connect(self._on_install_finished)

        self._current_progress_bar: QProgressBar | None = None
        self._current_status_label: QLabel | None = None

        self._init_ui()
        self.refresh_health()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Header
        top_box = QHBoxLayout()
        lbl_icon = QLabel("🩺")
        lbl_icon.setStyleSheet("font-size: 26px;")
        top_box.addWidget(lbl_icon)

        header_text_box = QVBoxLayout()
        self.lbl_overall = QLabel("Checking dependencies...")
        self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #cad3f5;")
        lbl_sub = QLabel("Automated diagnostic and 1-click dependency installer.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #a5adcb;")
        header_text_box.addWidget(self.lbl_overall)
        header_text_box.addWidget(lbl_sub)
        top_box.addLayout(header_text_box)
        top_box.addStretch()

        self.btn_refresh = QPushButton("↻ Recheck")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_health)
        top_box.addWidget(self.btn_refresh)
        main_layout.addLayout(top_box)

        # Hardware Profile Card
        self.hw_info = detect_system_hardware()
        hw_card = QFrame()
        hw_card.setObjectName("card_frame")
        hw_card.setStyleSheet("background-color: #1e2030; border: 1px solid #363a4f; border-radius: 8px; padding: 10px;")
        hw_layout = QHBoxLayout(hw_card)
        hw_layout.setContentsMargins(8, 4, 8, 4)

        lbl_hw_icon = QLabel("⚡" if self.hw_info["has_gpu"] else "💻")
        lbl_hw_icon.setStyleSheet("font-size: 20px;")
        hw_layout.addWidget(lbl_hw_icon)

        hw_text = QVBoxLayout()
        lbl_hw_title = QLabel(f"Hardware Profile: {self.hw_info['profile_title']} ({self.hw_info['device_type']})")
        lbl_hw_title.setStyleSheet("font-weight: 700; color: #8aadf4; font-size: 13px;")
        lbl_hw_sub = QLabel(f"Recommended Models: Whisper '{self.hw_info['recommended_whisper']}' · Ollama '{self.hw_info['recommended_ollama']}'")
        lbl_hw_sub.setStyleSheet("font-size: 11px; color: #b8c0e0;")
        hw_text.addWidget(lbl_hw_title)
        hw_text.addWidget(lbl_hw_sub)
        hw_layout.addLayout(hw_text, 1)

        main_layout.addWidget(hw_card)

        # Global Active Progress Bar (Hidden by default)
        self.global_progress = QProgressBar()
        self.global_progress.setFixedHeight(18)
        self.global_progress.setTextVisible(True)
        self.global_progress.hide()
        main_layout.addWidget(self.global_progress)

        self.lbl_install_status = QLabel("")
        self.lbl_install_status.setStyleSheet("color: #fab387; font-size: 12px; font-weight: 600;")
        self.lbl_install_status.hide()
        main_layout.addWidget(self.lbl_install_status)

        # Scroll area with cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll, 1)

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        main_layout.addLayout(btn_box)

    def refresh_health(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        result = run_full_system_check()
        overall = result["overall"]

        if overall == "ok":
            self.lbl_overall.setText("All Systems Ready")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #a6da95;")
        elif overall == "warning":
            self.lbl_overall.setText("System Ready with Warnings")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #fab387;")
        else:
            self.lbl_overall.setText("Dependencies Missing")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #ed8796;")

        for item in result["items"]:
            card = self._create_card(item)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _create_card(self, item: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card_frame")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        # Top row: Name + Badge
        top_row = QHBoxLayout()
        lbl_name = QLabel(item["name"])
        lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #cad3f5;")
        top_row.addWidget(lbl_name)
        top_row.addStretch()

        status = item["status"]
        if status == "ok":
            badge_text = "● READY"
            badge_color = "#a6da95"
            bg_color = "rgba(166, 218, 149, 0.15)"
        elif status == "warning":
            badge_text = "▲ ATTENTION"
            badge_color = "#fab387"
            bg_color = "rgba(250, 179, 135, 0.15)"
        else:
            badge_text = "✖ MISSING"
            badge_color = "#ed8796"
            bg_color = "rgba(237, 135, 150, 0.15)"

        lbl_badge = QLabel(badge_text)
        lbl_badge.setStyleSheet(
            f"font-weight: bold; font-size: 11px; color: {badge_color}; "
            f"background-color: {bg_color}; border-radius: 4px; padding: 2px 8px;"
        )
        top_row.addWidget(lbl_badge)
        layout.addLayout(top_row)

        # Title & Message
        lbl_title = QLabel(item["title"])
        lbl_title.setStyleSheet("font-weight: 500; color: #b8c0e0;")
        layout.addWidget(lbl_title)

        if item["message"]:
            lbl_msg = QLabel(item["message"])
            lbl_msg.setWordWrap(True)
            lbl_msg.setStyleSheet("color: #a5adcb; font-size: 12px;")
            layout.addWidget(lbl_msg)

        # Action / 1-Click Installer Button
        if status != "ok":
            action_row = QHBoxLayout()
            action_row.setSpacing(8)

            btn_auto = None
            if item["name"] == "FFmpeg Audio Engine":
                btn_auto = QPushButton("⬇ Download & Install FFmpeg (Automatic)")
                btn_auto.setStyleSheet("background-color: #8aadf4; color: #181926; font-weight: bold;")
                btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_auto.clicked.connect(lambda: self._start_install("ffmpeg"))
            elif "Ollama" in item["name"]:
                configured_model = config.get("ollama_model", "qwen2.5:7b")
                if not item.get("installed", False):
                    if sys.platform == "win32":
                        btn_auto = QPushButton("⬇ Download & Install Ollama (Windows)")
                        btn_auto.setStyleSheet("background-color: #8aadf4; color: #181926; font-weight: bold;")
                        btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
                        btn_auto.clicked.connect(lambda: self._start_install("ollama_service"))
                else:
                    # Service is running, pull the model
                    btn_auto = QPushButton(f"⬇ Download AI Model ({configured_model})")
                    btn_auto.setStyleSheet("background-color: #a6da95; color: #181926; font-weight: bold;")
                    btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_auto.clicked.connect(lambda: self._start_install("ollama_model", configured_model))

            if btn_auto:
                action_row.addWidget(btn_auto)

            layout.addLayout(action_row)

            # Manual Command Fallback Box
            action = item.get("action")
            if action:
                cmd_row = QHBoxLayout()
                lbl_cmd = QLabel(action)
                lbl_cmd.setWordWrap(True)
                lbl_cmd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lbl_cmd.setStyleSheet(
                    "background-color: #141520; border: 1px solid #363a4f; "
                    "border-radius: 6px; padding: 6px 10px; font-family: monospace; font-size: 11px; color: #cad3f5;"
                )
                cmd_row.addWidget(lbl_cmd, 1)

                btn_copy = QPushButton("Copy")
                btn_copy.setFixedWidth(55)
                btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_copy.clicked.connect(lambda _, a=action, b=btn_copy: self._copy_action(a, b))
                cmd_row.addWidget(btn_copy)
                layout.addLayout(cmd_row)

        return card

    def _start_install(self, task_type: str, payload: str | None = None):
        self.global_progress.setValue(0)
        self.global_progress.show()
        self.lbl_install_status.setText("Initializing automated installation...")
        self.lbl_install_status.show()
        self.btn_refresh.setEnabled(False)
        self.installer.start_install(task_type, payload)

    def _on_install_progress(self, pct: int, status_text: str):
        self.global_progress.setValue(pct)
        self.lbl_install_status.setText(status_text)

    def _on_install_finished(self, success: bool, msg: str):
        self.btn_refresh.setEnabled(True)
        if success:
            self.lbl_install_status.setText(f"✅ {msg}")
            self.global_progress.setValue(100)
            QTimer.singleShot(2500, self.global_progress.hide)
            QTimer.singleShot(4000, self.lbl_install_status.hide)
            self.refresh_health()
        else:
            self.lbl_install_status.setText(f"❌ Installation error: {msg}")
            self.global_progress.hide()

    def _copy_action(self, text: str, btn: QPushButton):
        QGuiApplication.clipboard().setText(text)
        orig = btn.text()
        btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: btn.setText(orig))
