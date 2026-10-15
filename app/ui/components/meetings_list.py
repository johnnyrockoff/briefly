import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import RECORDINGS_DIR, SUMMARIES_DIR, TRANSCRIPTS_DIR


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

        # Header
        top_bar = QHBoxLayout()
        lbl = QLabel("Recorded Meetings History")
        lbl.setStyleSheet("font-weight: 600; font-size: 14px; color: #cdd6f4;")
        top_bar.addWidget(lbl)
        top_bar.addStretch()

        btn_reload = QPushButton("🔄 Refresh List")
        btn_reload.clicked.connect(self.reload_meetings)
        top_bar.addWidget(btn_reload)
        layout.addLayout(top_bar)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Meeting / Date",
            "Size",
            "Transcription",
            "AI Summary",
            "Actions",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.table)

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

        self.table.setRowCount(len(sorted_stems))
        for row, stem in enumerate(sorted_stems):
            wav_path = RECORDINGS_DIR / f"{stem}.wav"
            txt_path = TRANSCRIPTS_DIR / f"{stem}.txt"
            md_path = SUMMARIES_DIR / f"{stem}.md"

            # Formata data legível
            display_name = stem.replace("reuniao_", "")
            try:
                dt = datetime.strptime(display_name, "%Y-%m-%d_%H-%M-%S")
                display_name = dt.strftime("%b %d, %Y at %H:%M:%S")
            except Exception:
                pass

            item_title = QTableWidgetItem(f"🎙️ {display_name}")
            item_title.setData(Qt.ItemDataRole.UserRole, stem)
            self.table.setItem(row, 0, item_title)

            # Tamanho do áudio
            if wav_path.exists():
                size_mb = wav_path.stat().st_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "-"
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_size)

            # Transcrição Status
            has_txt = txt_path.exists() and txt_path.stat().st_size > 0
            badge_txt = "✅ Ready" if has_txt else "⏳ Pending"
            item_txt = QTableWidgetItem(badge_txt)
            item_txt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if has_txt:
                item_txt.setForeground(Qt.GlobalColor.green)
            else:
                item_txt.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 2, item_txt)

            # Resumo Status
            has_md = md_path.exists() and md_path.stat().st_size > 0
            badge_md = "✅ Completed" if has_md else "⏳ Pending"
            item_md = QTableWidgetItem(badge_md)
            item_md.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if has_md:
                item_md.setForeground(Qt.GlobalColor.cyan)
            else:
                item_md.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 3, item_md)

            # Botões de Ação na Linha
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)

            btn_view = QPushButton("View")
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.clicked.connect(lambda _, s=stem: self.meeting_selected.emit(s))
            action_layout.addWidget(btn_view)

            if wav_path.exists():
                btn_trans = QPushButton("Transcribe" if not has_txt else "Retranscribe")
                btn_trans.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_trans.clicked.connect(lambda _, p=str(wav_path): self.transcribe_requested.emit(p))
                action_layout.addWidget(btn_trans)

            if has_txt:
                btn_sum = QPushButton("Summarize" if not has_md else "Regenerate")
                btn_sum.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_sum.clicked.connect(lambda _, p=str(txt_path): self.summarize_requested.emit(p))
                action_layout.addWidget(btn_sum)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Delete meeting and associated files")
            btn_del.setFixedWidth(30)
            btn_del.clicked.connect(lambda _, s=stem: self._confirm_delete(s))
            action_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 4, action_widget)

    def _on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        item_title = self.table.item(row, 0)
        if item_title:
            stem = item_title.data(Qt.ItemDataRole.UserRole)
            if stem:
                self.meeting_selected.emit(stem)

    def _confirm_delete(self, stem: str):
        reply = QMessageBox.question(
            self,
            "Delete Meeting",
            f"Are you sure you want to delete all files for meeting ({stem})?",
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
