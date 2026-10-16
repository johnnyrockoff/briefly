import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    DEFAULT_SYSTEM_PROMPT,
    _resolve_default_storage,
    config,
    get_storage_base,
)
from app.languages import INPUT_LANGUAGES, OUTPUT_LANGUAGES, get_prompt_for_language
from app.summarization.summarizer import get_available_ollama_models


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - Briefly")
        self.resize(640, 540)
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        # ==========================================
        # Tab 1: 📁 Storage & Files
        # ==========================================
        tab_storage = QWidget()
        layout_storage = QVBoxLayout(tab_storage)
        layout_storage.setSpacing(14)

        lbl_st_title = QLabel("Meeting Data & Storage Directory")
        lbl_st_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #cad3f5;")
        layout_storage.addWidget(lbl_st_title)

        lbl_st_info = QLabel(
            "Select the root folder where Briefly creates and manages your meeting data.\n"
            "Inside this folder, Briefly organizes files into subfolders: recordings/ (.wav audio), "
            "transcripts/ (.txt & .vtt text), and summaries/ (.md executive notes)."
        )
        lbl_st_info.setWordWrap(True)
        lbl_st_info.setStyleSheet("color: #a5adcb; font-size: 11px;")
        layout_storage.addWidget(lbl_st_info)

        # Folder picker row
        row_path = QHBoxLayout()
        self.txt_storage_dir = QLineEdit()
        self.txt_storage_dir.setPlaceholderText("Default: ~/Documents/Briefly")
        row_path.addWidget(self.txt_storage_dir, 1)

        btn_browse = QPushButton("📁 Browse...")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_storage_dir)
        row_path.addWidget(btn_browse)

        btn_reset_storage = QPushButton("Reset to Default")
        btn_reset_storage.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_storage.clicked.connect(self._reset_storage_dir)
        row_path.addWidget(btn_reset_storage)

        layout_storage.addLayout(row_path)

        # Quick action: Open Folder in OS file manager
        row_open = QHBoxLayout()
        btn_open_folder = QPushButton("📂 Open Storage Folder in File Manager")
        btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_folder.clicked.connect(self._open_storage_folder)
        row_open.addWidget(btn_open_folder)
        row_open.addStretch()
        layout_storage.addLayout(row_open)

        # Subfolders overview
        group_sub = QFrame()
        group_sub.setStyleSheet("background-color: rgba(30, 32, 48, 0.5); border-radius: 8px; padding: 10px;")
        layout_sub = QVBoxLayout(group_sub)
        layout_sub.setSpacing(6)

        lbl_sub_head = QLabel("Automatic Directory Structure:")
        lbl_sub_head.setStyleSheet("font-weight: bold; color: #8aadf4; font-size: 12px;")
        layout_sub.addWidget(lbl_sub_head)

        lbl_s1 = QLabel("• 🎙️ <b>recordings/</b> — 16 kHz normalized mono meeting audio recordings (.wav)")
        lbl_s1.setStyleSheet("color: #cad3f5; font-size: 11px;")
        layout_sub.addWidget(lbl_s1)

        lbl_s2 = QLabel("• 📝 <b>transcripts/</b> — Whisper offline transcripts (.txt) and timestamped subtitles (.vtt)")
        lbl_s2.setStyleSheet("color: #cad3f5; font-size: 11px;")
        layout_sub.addWidget(lbl_s2)

        lbl_s3 = QLabel("• 📋 <b>summaries/</b> — Local Ollama AI structured executive notes in Markdown (.md)")
        lbl_s3.setStyleSheet("color: #cad3f5; font-size: 11px;")
        layout_sub.addWidget(lbl_s3)

        layout_storage.addWidget(group_sub)
        layout_storage.addStretch()

        self.tabs.addTab(tab_storage, "📁 Storage")

        # ==========================================
        # Tab 2: 🌐 Languages (Input & Output)
        # ==========================================
        tab_lang = QWidget()
        form_lang = QFormLayout(tab_lang)
        form_lang.setSpacing(14)

        # Spoken Language (Input for Whisper)
        self.combo_input_lang = QComboBox()
        for code, label in INPUT_LANGUAGES:
            self.combo_input_lang.addItem(label, code)
        form_lang.addRow("🗣️ Meeting Spoken Language (Input):", self.combo_input_lang)

        lbl_hint_in = QLabel("Specifies the language spoken in meetings. Setting a specific language improves Whisper accuracy and eliminates language switching.")
        lbl_hint_in.setWordWrap(True)
        lbl_hint_in.setStyleSheet("color: #a5adcb; font-size: 11px;")
        form_lang.addRow("", lbl_hint_in)

        # Summary Language (Output for Ollama)
        self.combo_output_lang = QComboBox()
        for code, label in OUTPUT_LANGUAGES:
            self.combo_output_lang.addItem(label, code)
        self.combo_output_lang.currentIndexChanged.connect(self._on_output_lang_changed)
        form_lang.addRow("📋 Summary Output Language:", self.combo_output_lang)

        lbl_hint_out = QLabel("The language in which AI meeting summaries, executive briefings, and action item tables will be drafted.")
        lbl_hint_out.setWordWrap(True)
        lbl_hint_out.setStyleSheet("color: #a5adcb; font-size: 11px;")
        form_lang.addRow("", lbl_hint_out)

        btn_sync_prompt = QPushButton("Apply Template for Selected Language")
        btn_sync_prompt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sync_prompt.clicked.connect(self._apply_language_prompt_template)
        form_lang.addRow("", btn_sync_prompt)

        self.tabs.addTab(tab_lang, "🌐 Languages")

        # ==========================================
        # Tab 2: 🧠 AI Models (Whisper & Ollama)
        # ==========================================
        tab_ai = QWidget()
        form_ai = QFormLayout(tab_ai)
        form_ai.setSpacing(10)

        # Whisper Model
        self.combo_whisper_model = QComboBox()
        self.combo_whisper_model.addItems(["tiny", "base", "small", "medium", "large-v3", "turbo"])
        form_ai.addRow("Whisper Model (Transcription):", self.combo_whisper_model)

        # Whisper Device
        self.combo_whisper_device = QComboBox()
        self.combo_whisper_device.addItem("NVIDIA GPU (CUDA)", "cuda")
        self.combo_whisper_device.addItem("Processor (CPU)", "cpu")
        form_ai.addRow("Execution Device:", self.combo_whisper_device)

        # Ollama URL
        self.txt_ollama_url = QLineEdit()
        form_ai.addRow("Ollama URL:", self.txt_ollama_url)

        # Ollama Model + Refresh button
        ollama_model_layout = QHBoxLayout()
        self.combo_ollama_model = QComboBox()
        self.combo_ollama_model.setEditable(True)
        ollama_model_layout.addWidget(self.combo_ollama_model, 1)

        btn_refresh_ollama = QPushButton("Detect Models")
        btn_refresh_ollama.clicked.connect(self._refresh_ollama_models)
        ollama_model_layout.addWidget(btn_refresh_ollama)
        form_ai.addRow("Ollama Model (Summary):", ollama_model_layout)

        # Context length (num_ctx)
        self.spin_num_ctx = QSpinBox()
        self.spin_num_ctx.setRange(2048, 65536)
        self.spin_num_ctx.setSingleStep(2048)
        form_ai.addRow("Context Length (Tokens):", self.spin_num_ctx)

        self.tabs.addTab(tab_ai, "🧠 AI Models")

        # ==========================================
        # Tab 3: 📝 Summary Prompt Editor
        # ==========================================
        tab_prompt = QWidget()
        layout_prompt = QVBoxLayout(tab_prompt)
        lbl_p_info = QLabel("Instructions passed to Ollama for structured summary formatting:")
        lbl_p_info.setStyleSheet("color: #a5adcb; font-size: 11px;")
        layout_prompt.addWidget(lbl_p_info)

        self.txt_system_prompt = QTextEdit()
        layout_prompt.addWidget(self.txt_system_prompt)

        btn_reset_prompt = QPushButton("Restore Default Template")
        btn_reset_prompt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_prompt.clicked.connect(self._apply_language_prompt_template)
        layout_prompt.addWidget(btn_reset_prompt, 0, Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(tab_prompt, "📝 Prompt Template")

        # ==========================================
        # Tab 4: ⚙️ Automation & Window
        # ==========================================
        tab_system = QWidget()
        layout_sys = QVBoxLayout(tab_system)
        layout_sys.setSpacing(12)

        self.chk_auto_transcribe = QCheckBox("Automatically transcribe after recording ends")
        layout_sys.addWidget(self.chk_auto_transcribe)

        self.chk_auto_summarize = QCheckBox("Automatically generate AI summary after transcription finishes")
        layout_sys.addWidget(self.chk_auto_summarize)

        self.chk_minimize_tray = QCheckBox("Minimize to system tray when closing the main window")
        layout_sys.addWidget(self.chk_minimize_tray)

        layout_sys.addStretch()
        self.tabs.addTab(tab_system, "⚙️ Automation & Window")

        layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("btn_primary_action")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_values)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _browse_storage_dir(self):
        current = self.txt_storage_dir.text().strip() or str(get_storage_base())
        chosen = QFileDialog.getExistingDirectory(self, "Select Storage Directory for Briefly", current)
        if chosen:
            self.txt_storage_dir.setText(chosen)

    def _reset_storage_dir(self):
        default_dir = _resolve_default_storage()
        self.txt_storage_dir.setText(str(default_dir))

    def _open_storage_folder(self):
        folder = Path(self.txt_storage_dir.text().strip() or str(get_storage_base()))
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:
            QMessageBox.warning(self, "Open Folder", f"Could not open directory: {e}")

    def _load_values(self):
        # Storage
        saved_storage = config.get("storage_dir", "")
        if saved_storage:
            self.txt_storage_dir.setText(saved_storage)
        else:
            self.txt_storage_dir.setText(str(get_storage_base()))

        # Languages
        saved_in = config.get("input_language", "auto")
        idx_in = self.combo_input_lang.findData(saved_in)
        if idx_in >= 0:
            self.combo_input_lang.setCurrentIndex(idx_in)

        saved_out = config.get("output_language", "pt")
        idx_out = self.combo_output_lang.findData(saved_out)
        if idx_out >= 0:
            self.combo_output_lang.setCurrentIndex(idx_out)

        # Whisper
        cur_whisper = config.get("whisper_model", "small")
        idx_w = self.combo_whisper_model.findText(cur_whisper)
        if idx_w >= 0:
            self.combo_whisper_model.setCurrentIndex(idx_w)

        cur_device = config.get("whisper_device", "cuda")
        idx_d = self.combo_whisper_device.findData(cur_device)
        if idx_d >= 0:
            self.combo_whisper_device.setCurrentIndex(idx_d)

        # Ollama
        self.txt_ollama_url.setText(config.get("ollama_url", "http://localhost:11434/api/chat"))
        self.spin_num_ctx.setValue(int(config.get("num_ctx", 8192)))

        self._refresh_ollama_models()

        # Prompt
        saved_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT).strip()
        from app.languages import LEGACY_PROMPT_SIGNATURES
        if any(sig in saved_prompt for sig in LEGACY_PROMPT_SIGNATURES):
            saved_prompt = get_prompt_for_language(saved_out)
        self.txt_system_prompt.setPlainText(saved_prompt)

        # Checkboxes
        self.chk_auto_transcribe.setChecked(bool(config.get("auto_transcribe", True)))
        self.chk_auto_summarize.setChecked(bool(config.get("auto_summarize", True)))
        self.chk_minimize_tray.setChecked(bool(config.get("minimize_to_tray_on_close", True)))

    def _refresh_ollama_models(self):
        cur_model = config.get("ollama_model", "qwen2.5:7b")
        models = get_available_ollama_models()
        self.combo_ollama_model.clear()
        for m in models:
            self.combo_ollama_model.addItem(m)
        idx = self.combo_ollama_model.findText(cur_model)
        if idx >= 0:
            self.combo_ollama_model.setCurrentIndex(idx)
        else:
            self.combo_ollama_model.setEditText(cur_model)

    def _on_output_lang_changed(self, index: int):
        target_lang = self.combo_output_lang.currentData() or "pt"
        cur_prompt = self.txt_system_prompt.toPlainText().strip()
        from app.languages import LEGACY_PROMPT_SIGNATURES, PROMPTS_BY_LANGUAGE
        if (
            not cur_prompt
            or any(cur_prompt == p.strip() for p in PROMPTS_BY_LANGUAGE.values())
            or any(sig in cur_prompt for sig in LEGACY_PROMPT_SIGNATURES)
        ):
            self.txt_system_prompt.setPlainText(get_prompt_for_language(target_lang))

    def _apply_language_prompt_template(self):
        target_lang = self.combo_output_lang.currentData() or "pt"
        template = get_prompt_for_language(target_lang)
        self.txt_system_prompt.setPlainText(template)

    def _save_values(self):
        # Storage
        new_storage = self.txt_storage_dir.text().strip()
        default_storage = str(_resolve_default_storage())
        if not new_storage or new_storage == default_storage:
            config.set("storage_dir", "")
        else:
            config.set("storage_dir", new_storage)

        config.set("input_language", self.combo_input_lang.currentData())
        config.set("output_language", self.combo_output_lang.currentData())
        config.set("whisper_model", self.combo_whisper_model.currentText())
        config.set("whisper_device", self.combo_whisper_device.currentData())
        config.set("ollama_url", self.txt_ollama_url.text().strip())
        config.set("ollama_model", self.combo_ollama_model.currentText().strip())
        config.set("num_ctx", self.spin_num_ctx.value())
        config.set("system_prompt", self.txt_system_prompt.toPlainText())
        config.set("auto_transcribe", self.chk_auto_transcribe.isChecked())
        config.set("auto_summarize", self.chk_auto_summarize.isChecked())
        config.set("minimize_to_tray_on_close", self.chk_minimize_tray.isChecked())
        self.accept()
