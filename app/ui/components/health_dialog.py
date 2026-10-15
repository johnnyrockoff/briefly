from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.health import run_full_system_check


class HealthCheckDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Health & Dependencies")
        self.resize(620, 520)
        self._init_ui()
        self.refresh_health()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)

        # Header
        top_box = QHBoxLayout()
        lbl_icon = QLabel("🩺")
        lbl_icon.setStyleSheet("font-size: 26px;")
        top_box.addWidget(lbl_icon)

        header_text_box = QVBoxLayout()
        self.lbl_overall = QLabel("Checking dependencies...")
        self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        lbl_sub = QLabel("Verification of required Linux audio backends and AI engines.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #a6adc8;")
        header_text_box.addWidget(self.lbl_overall)
        header_text_box.addWidget(lbl_sub)
        top_box.addLayout(header_text_box)
        top_box.addStretch()

        self.btn_refresh = QPushButton("🔄 Recheck")
        self.btn_refresh.clicked.connect(self.refresh_health)
        top_box.addWidget(self.btn_refresh)
        main_layout.addLayout(top_box)

        # Scroll area com a lista de cards
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
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        main_layout.addLayout(btn_box)

    def refresh_health(self):
        # Limpar cards anteriores
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        result = run_full_system_check()
        overall = result["overall"]

        if overall == "ok":
            self.lbl_overall.setText("All Systems Ready")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #a6e3a1;")
        elif overall == "warning":
            self.lbl_overall.setText("System Ready with Warnings")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #fab387;")
        else:
            self.lbl_overall.setText("Dependencies Missing")
            self.lbl_overall.setStyleSheet("font-size: 16px; font-weight: bold; color: #f38ba8;")

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
        lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #cdd6f4;")
        top_row.addWidget(lbl_name)
        top_row.addStretch()

        status = item["status"]
        if status == "ok":
            badge_text = "● READY"
            badge_color = "#a6e3a1"
        elif status == "warning":
            badge_text = "▲ ATTENTION"
            badge_color = "#fab387"
        else:
            badge_text = "✖ MISSING"
            badge_color = "#f38ba8"

        lbl_badge = QLabel(badge_text)
        lbl_badge.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {badge_color};")
        top_row.addWidget(lbl_badge)
        layout.addLayout(top_row)

        # Title & Message
        lbl_title = QLabel(item["title"])
        lbl_title.setStyleSheet("font-weight: 500; color: #bac2de;")
        layout.addWidget(lbl_title)

        if item["message"]:
            lbl_msg = QLabel(item["message"])
            lbl_msg.setWordWrap(True)
            lbl_msg.setStyleSheet("color: #a6adc8; font-size: 12px;")
            layout.addWidget(lbl_msg)

        # Suggested Action / Command
        action = item.get("action")
        if action:
            act_box = QVBoxLayout()
            lbl_hint = QLabel("Suggested action to resolve:")
            lbl_hint.setStyleSheet("font-size: 11px; color: #89b4fa; font-weight: 600; margin-top: 4px;")
            act_box.addWidget(lbl_hint)

            cmd_row = QHBoxLayout()
            lbl_cmd = QLabel(action)
            lbl_cmd.setWordWrap(True)
            lbl_cmd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_cmd.setStyleSheet(
                "background-color: #11111b; border: 1px solid #313244; "
                "border-radius: 6px; padding: 6px 10px; font-family: monospace; font-size: 12px; color: #f38ba8;"
            )
            cmd_row.addWidget(lbl_cmd, 1)

            btn_copy = QPushButton("Copy")
            btn_copy.setFixedWidth(60)
            btn_copy.clicked.connect(lambda _, a=action, b=btn_copy: self._copy_action(a, b))
            cmd_row.addWidget(btn_copy)

            act_box.addLayout(cmd_row)
            layout.addLayout(act_box)

        return card

    def _copy_action(self, text: str, btn: QPushButton):
        QGuiApplication.clipboard().setText(text)
        orig = btn.text()
        btn.setText("Copied!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: btn.setText(orig))
