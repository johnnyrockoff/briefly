import subprocess
from pathlib import Path
from typing import Optional

import markdown
from PySide6.QtCore import Qt
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

from app.config import SUMMARIES_DIR, TRANSCRIPTS_DIR
from app.ui.styles import MARKDOWN_HTML_STYLE


class MeetingViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stem: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header com título da reunião selecionada e botões de ação
        header = QHBoxLayout()
        self.lbl_title = QLabel("Select a meeting to view the summary")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #89b4fa;")
        header.addWidget(self.lbl_title)
        header.addStretch()

        self.btn_copy_markdown = QPushButton("📋 Copy Markdown")
        self.btn_copy_markdown.setToolTip("Copy full markdown summary to clipboard")
        self.btn_copy_markdown.clicked.connect(self._copy_markdown)
        self.btn_copy_markdown.setEnabled(False)
        header.addWidget(self.btn_copy_markdown)

        self.btn_open_external = QPushButton("↗ Open in Editor")
        self.btn_open_external.setToolTip("Open .md file in Linux default editor (Gedit, VSCode, etc.)")
        self.btn_open_external.clicked.connect(self._open_in_editor)
        self.btn_open_external.setEnabled(False)
        header.addWidget(self.btn_open_external)

        layout.addLayout(header)

        # Barra de status / progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminado por padrão
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #fab387; font-size: 12px;")
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        # Abas de visualização
        self.tabs = QTabWidget()

        # Aba 1: Resumo Formatado (HTML do Markdown)
        self.browser_summary = QTextBrowser()
        self.browser_summary.setOpenExternalLinks(True)
        self.tabs.addTab(self.browser_summary, "📋 Meeting Summary")

        # Aba 2: Resumo em Markdown Puro (para edição rápida)
        self.edit_raw_markdown = QTextEdit()
        self.edit_raw_markdown.textChanged.connect(self._on_raw_markdown_edited)
        self.tabs.addTab(self.edit_raw_markdown, "✏️ Raw Markdown")

        # Aba 3: Transcrição Completa
        self.browser_transcript = QTextBrowser()
        self.tabs.addTab(self.browser_transcript, "📝 Full Transcript")

        layout.addWidget(self.tabs)

    def load_meeting(self, stem: str):
        self.current_stem = stem
        display_name = stem.replace("reuniao_", "")
        self.lbl_title.setText(f"Meeting: {display_name}")

        txt_path = TRANSCRIPTS_DIR / f"{stem}.txt"
        md_path = SUMMARIES_DIR / f"{stem}.md"

        # Carregar transcrição
        if txt_path.exists():
            transcript_text = txt_path.read_text(encoding="utf-8").strip()
            self.browser_transcript.setPlainText(transcript_text if transcript_text else "(Empty transcript)")
        else:
            self.browser_transcript.setPlainText("No transcript available for this recording. Click 'Transcribe'.")

        # Carregar resumo
        if md_path.exists():
            md_content = md_path.read_text(encoding="utf-8").strip()
            self.edit_raw_markdown.blockSignals(True)
            self.edit_raw_markdown.setPlainText(md_content)
            self.edit_raw_markdown.blockSignals(False)
            self._render_markdown_html(md_content)
            self.btn_copy_markdown.setEnabled(True)
            self.btn_open_external.setEnabled(True)
        else:
            self.edit_raw_markdown.blockSignals(True)
            self.edit_raw_markdown.setPlainText("")
            self.edit_raw_markdown.blockSignals(False)
            self.browser_summary.setHtml(
                f"{MARKDOWN_HTML_STYLE}<p style='color: #a6adc8;'>No summary generated yet. "
                "Click <b>'Summarize'</b> to process with local AI.</p>"
            )
            self.btn_copy_markdown.setEnabled(False)
            self.btn_open_external.setEnabled(False)

    def set_processing_status(self, message: str, in_progress: bool = True):
        if in_progress:
            self.lbl_status.setText(f"⏳ {message}")
            self.lbl_status.show()
            self.progress_bar.show()
        else:
            self.lbl_status.setText(f"✅ {message}")
            self.progress_bar.hide()

    def hide_processing_status(self):
        self.lbl_status.hide()
        self.progress_bar.hide()

    def _render_markdown_html(self, md_content: str):
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
        )
        full_html = f"{MARKDOWN_HTML_STYLE}<body>{html_body}</body>"
        self.browser_summary.setHtml(full_html)

    def _on_raw_markdown_edited(self):
        # Quando o usuário edita a aba de markdown puro, atualiza o HTML e salva
        if not self.current_stem:
            return
        content = self.edit_raw_markdown.toPlainText()
        self._render_markdown_html(content)
        md_path = SUMMARIES_DIR / f"{self.current_stem}.md"
        try:
            md_path.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def _copy_markdown(self):
        content = self.edit_raw_markdown.toPlainText()
        if content:
            QGuiApplication.clipboard().setText(content)
            original_text = self.btn_copy_markdown.text()
            self.btn_copy_markdown.setText("✅ Copied!")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_copy_markdown.setText(original_text))

    def _open_in_editor(self):
        if not self.current_stem:
            return
        md_path = SUMMARIES_DIR / f"{self.current_stem}.md"
        if md_path.exists():
            subprocess.Popen(["xdg-open", str(md_path)])
