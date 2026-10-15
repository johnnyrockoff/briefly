from datetime import datetime
from pathlib import Path
import subprocess
from typing import Optional

import markdown
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import get_recordings_dir, get_summaries_dir, get_transcripts_dir
from app.ui.styles import MARKDOWN_HTML_STYLE


class MeetingViewer(QWidget):
    transcribe_requested = Signal(str)  # wav_path
    summarize_requested = Signal(str)   # txt_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stem: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header with selected meeting title and actions
        header = QHBoxLayout()
        header.setSpacing(8)

        self.lbl_title = QLabel("Select a meeting to view details")
        self.lbl_title.setStyleSheet("font-weight: 700; font-size: 15px; color: #8aadf4;")
        header.addWidget(self.lbl_title)
        header.addStretch()

        # Action Buttons
        self.btn_transcribe = QPushButton("🎙️ Transcribe")
        self.btn_transcribe.setToolTip("Run speech-to-text with local Whisper")
        self.btn_transcribe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_transcribe.clicked.connect(self._on_transcribe_clicked)
        self.btn_transcribe.setEnabled(False)
        header.addWidget(self.btn_transcribe)

        self.btn_summarize = QPushButton("✨ Summarize")
        self.btn_summarize.setToolTip("Generate AI summary with local Ollama")
        self.btn_summarize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_summarize.clicked.connect(self._on_summarize_clicked)
        self.btn_summarize.setEnabled(False)
        header.addWidget(self.btn_summarize)

        self.btn_copy_markdown = QPushButton("📋 Copy")
        self.btn_copy_markdown.setToolTip("Copy full markdown summary to clipboard")
        self.btn_copy_markdown.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_markdown.clicked.connect(self._copy_markdown)
        self.btn_copy_markdown.setEnabled(False)
        header.addWidget(self.btn_copy_markdown)

        self.btn_open_external = QPushButton("↗ Open")
        self.btn_open_external.setToolTip("Open markdown file in default text editor")
        self.btn_open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_external.clicked.connect(self._open_in_editor)
        self.btn_open_external.setEnabled(False)
        header.addWidget(self.btn_open_external)

        layout.addLayout(header)

        # Progress / Status Banner
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #fab387; font-size: 12px; font-weight: 500;")
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        # View Tabs
        self.tabs = QTabWidget()

        # Tab 1: Formatted Summary (Markdown HTML)
        self.browser_summary = QTextBrowser()
        self.browser_summary.setOpenExternalLinks(True)
        self.tabs.addTab(self.browser_summary, "📋 Meeting Summary")

        # Tab 2: Raw Markdown Editor
        self.edit_raw_markdown = QTextEdit()
        self.edit_raw_markdown.textChanged.connect(self._on_raw_markdown_edited)
        self.tabs.addTab(self.edit_raw_markdown, "✏️ Raw Markdown")

        # Tab 3: Full Transcript
        self.browser_transcript = QTextBrowser()
        self.tabs.addTab(self.browser_transcript, "📝 Full Transcript")

        layout.addWidget(self.tabs)

    def load_meeting(self, stem: str):
        self.current_stem = stem

        # Formatted title
        raw_name = stem.replace("reuniao_", "")
        display_name = raw_name
        try:
            dt = datetime.strptime(raw_name, "%Y-%m-%d_%H-%M-%S")
            display_name = dt.strftime("%b %d, %Y · %H:%M:%S")
        except Exception:
            pass
        self.lbl_title.setText(f"Meeting: {display_name}")

        wav_path = get_recordings_dir() / f"{stem}.wav"
        txt_path = get_transcripts_dir() / f"{stem}.txt"
        md_path = get_summaries_dir() / f"{stem}.md"

        has_wav = wav_path.exists()
        has_txt = txt_path.exists() and txt_path.stat().st_size > 0
        has_md = md_path.exists() and md_path.stat().st_size > 0

        self.btn_transcribe.setEnabled(has_wav)
        self.btn_summarize.setEnabled(has_txt)
        self.btn_copy_markdown.setEnabled(has_md)
        self.btn_open_external.setEnabled(has_md)

        # Load transcript
        if txt_path.exists():
            transcript_text = txt_path.read_text(encoding="utf-8").strip()
            self.browser_transcript.setPlainText(transcript_text if transcript_text else "(Empty transcript)")
        else:
            if has_wav:
                self.browser_transcript.setPlainText(
                    "Audio recording is available, but not yet transcribed.\n"
                    "Click '🎙️ Transcribe' above to run Whisper speech-to-text."
                )
            else:
                self.browser_transcript.setPlainText("No audio or transcript available for this entry.")

        # Load summary
        if md_path.exists():
            md_content = md_path.read_text(encoding="utf-8").strip()
            self.edit_raw_markdown.blockSignals(True)
            self.edit_raw_markdown.setPlainText(md_content)
            self.edit_raw_markdown.blockSignals(False)
            self._render_markdown_html(md_content)
        else:
            self.edit_raw_markdown.blockSignals(True)
            self.edit_raw_markdown.setPlainText("")
            self.edit_raw_markdown.blockSignals(False)
            if has_txt:
                hint = "Click <b>'✨ Summarize'</b> in the toolbar above to generate meeting notes with local AI."
            elif has_wav:
                hint = "First click <b>'🎙️ Transcribe'</b> to generate a transcript, then generate the summary."
            else:
                hint = "No audio or transcript found for this meeting."

            self.browser_summary.setHtml(
                f"{MARKDOWN_HTML_STYLE}<div style='padding: 24px; text-align: center; color: #a5adcb;'>"
                f"<h3 style='color: #8aadf4;'>No Summary Generated Yet</h3>"
                f"<p>{hint}</p></div>"
            )

    def clear(self):
        self.current_stem = None
        self.lbl_title.setText("Select a Meeting")
        self.btn_transcribe.setEnabled(False)
        self.btn_summarize.setEnabled(False)
        self.btn_copy_markdown.setEnabled(False)
        self.btn_open_external.setEnabled(False)
        self.browser_transcript.setPlainText("Select a meeting from the list on the left to view its transcript.")
        self.edit_raw_markdown.blockSignals(True)
        self.edit_raw_markdown.setPlainText("")
        self.edit_raw_markdown.blockSignals(False)
        self.browser_summary.setHtml(
            f"{MARKDOWN_HTML_STYLE}<div style='padding: 24px; text-align: center; color: #a5adcb;'>"
            f"<h3 style='color: #8aadf4;'>No Meeting Selected</h3>"
            f"<p>Select a meeting from the list or start a new recording.</p></div>"
        )

    def set_processing_status(self, message: str, in_progress: bool = True):
        if in_progress:
            self.lbl_status.setText(f"⏳ {message}")
            self.lbl_status.show()
            self.progress_bar.show()
            self.btn_transcribe.setEnabled(False)
            self.btn_summarize.setEnabled(False)
        else:
            self.lbl_status.setText(f"✅ {message}")
            self.progress_bar.hide()
            if self.current_stem:
                self.load_meeting(self.current_stem)

    def hide_processing_status(self):
        self.lbl_status.hide()
        self.progress_bar.hide()
        if self.current_stem:
            self.load_meeting(self.current_stem)

    def _render_markdown_html(self, md_content: str):
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
        )
        full_html = f"{MARKDOWN_HTML_STYLE}<body>{html_body}</body>"
        self.browser_summary.setHtml(full_html)

    def _on_raw_markdown_edited(self):
        if not self.current_stem:
            return
        content = self.edit_raw_markdown.toPlainText()
        self._render_markdown_html(content)
        md_path = get_summaries_dir() / f"{self.current_stem}.md"
        try:
            md_path.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def _on_transcribe_clicked(self):
        if not self.current_stem:
            return
        wav_path = get_recordings_dir() / f"{self.current_stem}.wav"
        if wav_path.exists():
            self.transcribe_requested.emit(str(wav_path))

    def _on_summarize_clicked(self):
        if not self.current_stem:
            return
        txt_path = get_transcripts_dir() / f"{self.current_stem}.txt"
        if txt_path.exists():
            self.summarize_requested.emit(str(txt_path))

    def _copy_markdown(self):
        content = self.edit_raw_markdown.toPlainText()
        if content:
            QGuiApplication.clipboard().setText(content)
            original_text = self.btn_copy_markdown.text()
            self.btn_copy_markdown.setText("✅ Copied!")
            QTimer.singleShot(2000, lambda: self.btn_copy_markdown.setText(original_text))

    def _open_in_editor(self):
        if not self.current_stem:
            return
        md_path = get_summaries_dir() / f"{self.current_stem}.md"
        if md_path.exists():
            import sys
            import os
            if sys.platform == "win32":
                os.startfile(str(md_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(md_path)])
            else:
                subprocess.Popen(["xdg-open", str(md_path)])
