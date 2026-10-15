from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import RECORDINGS_DIR, SUMMARIES_DIR, TRANSCRIPTS_DIR


class MeetingItemWidget(QWidget):
    """Custom rich widget for each meeting in the sidebar list."""
    delete_clicked = Signal(str)

    def __init__(self, stem: str, parent=None):
        super().__init__(parent)
        self.stem = stem
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        wav_path = RECORDINGS_DIR / f"{self.stem}.wav"
        txt_path = TRANSCRIPTS_DIR / f"{self.stem}.txt"
        md_path = SUMMARIES_DIR / f"{self.stem}.md"

        # Format title & date
        raw_name = self.stem.replace("reuniao_", "")
        display_date = raw_name
        try:
            dt = datetime.strptime(raw_name, "%Y-%m-%d_%H-%M-%S")
            display_date = dt.strftime("%b %d, %Y · %H:%M")
        except Exception:
            pass

        # Top row: Title + Delete button
        top_row = QHBoxLayout()
        lbl_icon = QLabel("🎙️")
        lbl_icon.setStyleSheet("font-size: 13px;")
        top_row.addWidget(lbl_icon)

        self.lbl_title = QLabel(display_date)
        self.lbl_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #cad3f5;")
        top_row.addWidget(self.lbl_title, 1)

        btn_del = QPushButton("✕")
        btn_del.setToolTip("Delete meeting files")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #6e738d; font-weight: bold; padding: 0px; } "
            "QPushButton:hover { color: #ed8796; background: rgba(237, 135, 150, 0.15); border-radius: 10px; }"
        )
        btn_del.clicked.connect(lambda: self.delete_clicked.emit(self.stem))
        top_row.addWidget(btn_del)
        layout.addLayout(top_row)

        # Bottom row: Status Pills & Audio Size
        pills_row = QHBoxLayout()
        pills_row.setSpacing(6)

        # Audio file size
        if wav_path.exists():
            mb = wav_path.stat().st_size / (1024 * 1024)
            lbl_size = QLabel(f"{mb:.1f} MB")
        else:
            lbl_size = QLabel("Text only")
        lbl_size.setStyleSheet("font-size: 11px; color: #a5adcb;")
        pills_row.addWidget(lbl_size)

        # Transcript Chip
        has_txt = txt_path.exists() and txt_path.stat().st_size > 0
        if has_txt:
            pill_txt = QLabel("Transcript")
            pill_txt.setStyleSheet(
                "background-color: rgba(166, 218, 149, 0.15); color: #a6da95; "
                "font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 6px;"
            )
        else:
            pill_txt = QLabel("No Text")
            pill_txt.setStyleSheet(
                "background-color: rgba(110, 115, 141, 0.2); color: #8087a2; "
                "font-size: 10px; border-radius: 4px; padding: 1px 6px;"
            )
        pills_row.addWidget(pill_txt)

        # Summary Chip
        has_md = md_path.exists() and md_path.stat().st_size > 0
        if has_md:
            pill_sum = QLabel("Summary")
            pill_sum.setStyleSheet(
                "background-color: rgba(138, 173, 244, 0.15); color: #8aadf4; "
                "font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 6px;"
            )
        else:
            pill_sum = QLabel("No Summary")
            pill_sum.setStyleSheet(
                "background-color: rgba(110, 115, 141, 0.2); color: #8087a2; "
                "font-size: 10px; border-radius: 4px; padding: 1px 6px;"
            )
        pills_row.addWidget(pill_sum)

        pills_row.addStretch()
        layout.addLayout(pills_row)


class MeetingsList(QWidget):
    meeting_selected = Signal(str)  # stem
    transcribe_requested = Signal(str)  # wav_path
    summarize_requested = Signal(str)  # txt_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.reload_meetings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header with Title and Refresh
        header = QHBoxLayout()
        self.lbl_count = QLabel("Meetings")
        self.lbl_count.setStyleSheet("font-weight: 700; font-size: 13px; color: #cad3f5;")
        header.addWidget(self.lbl_count)
        header.addStretch()

        btn_refresh = QPushButton("↻")
        btn_refresh.setObjectName("icon_btn")
        btn_refresh.setToolTip("Refresh meetings list")
        btn_refresh.setFixedSize(30, 28)
        btn_refresh.clicked.connect(self.reload_meetings)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Search filter
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Filter meetings...")
        self.txt_filter.textChanged.connect(self._filter_list)
        layout.addWidget(self.txt_filter)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("meetings_list_widget")
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget, 1)

    def reload_meetings(self):
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

        stems = set()
        for f in RECORDINGS_DIR.glob("*.wav"):
            stems.add(f.stem)
        for f in TRANSCRIPTS_DIR.glob("*.txt"):
            stems.add(f.stem)
        for f in SUMMARIES_DIR.glob("*.md"):
            stems.add(f.stem)

        sorted_stems = sorted(list(stems), reverse=True)
        self.lbl_count.setText(f"Meetings ({len(sorted_stems)})")

        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        for stem in sorted_stems:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, stem)

            widget = MeetingItemWidget(stem)
            widget.delete_clicked.connect(self._confirm_delete)

            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        self.list_widget.blockSignals(False)

        # Reselect first if items exist
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_list(self, query: str):
        query = query.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            stem = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(query not in stem.lower())

    def _on_selection_changed(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            stem = current_item.data(Qt.ItemDataRole.UserRole)
            if stem:
                self.meeting_selected.emit(stem)

    def get_first_stem(self) -> Optional[str]:
        if self.list_widget.count() > 0:
            first = self.list_widget.item(0)
            return first.data(Qt.ItemDataRole.UserRole)
        return None

    def _confirm_delete(self, stem: str):
        reply = QMessageBox.question(
            self,
            "Delete Meeting",
            f"Are you sure you want to delete all files for meeting:\n{stem}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for p in [
                RECORDINGS_DIR / f"{stem}.wav",
                TRANSCRIPTS_DIR / f"{stem}.txt",
                TRANSCRIPTS_DIR / f"{stem}.vtt",
                SUMMARIES_DIR / f"{stem}.md",
            ]:
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
            self.reload_meetings()
