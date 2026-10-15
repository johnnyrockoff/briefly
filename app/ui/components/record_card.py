from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.audio.devices import (
    get_default_sink,
    get_default_source,
    list_microphones,
    list_sinks,
)
from app.config import config
from app.languages import INPUT_LANGUAGES, OUTPUT_LANGUAGES


class RecordCard(QFrame):
    start_requested = Signal()
    stop_requested = Signal()
    devices_changed = Signal()
    languages_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        self._init_ui()
        self.refresh_devices()
        self.refresh_languages()
        self.set_recording_state(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header com título e status badge
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("Recording Studio")
        self.lbl_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #cad3f5;")
        top_bar.addWidget(self.lbl_title)

        self.lbl_status_badge = QLabel("● READY")
        self.lbl_status_badge.setStyleSheet(
            "color: #a6da95; background-color: rgba(166, 218, 149, 0.15); "
            "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
        )
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_status_badge)
        layout.addLayout(top_bar)

        # Timer Display em destaque
        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setObjectName("lbl_timer_idle")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_timer)

        # Botão Principal Gravar / Parar
        self.btn_record = QPushButton("▶ Start Recording")
        self.btn_record.setObjectName("btn_record_start")
        self.btn_record.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_record.setFixedHeight(42)
        self.btn_record.clicked.connect(self._toggle_recording)
        layout.addWidget(self.btn_record)

        # Dispositivos de Áudio
        dev_container = QVBoxLayout()
        dev_container.setSpacing(8)

        # Monitor (Áudio da Reunião / Fone)
        lbl_mon = QLabel("🔊 System Audio (Participants):")
        lbl_mon.setObjectName("lbl_field_header")
        dev_container.addWidget(lbl_mon)

        mon_row = QHBoxLayout()
        self.combo_monitor = QComboBox()
        self.combo_monitor.currentIndexChanged.connect(self._on_monitor_changed)
        mon_row.addWidget(self.combo_monitor, 1)

        btn_refresh = QPushButton("↻")
        btn_refresh.setObjectName("icon_btn")
        btn_refresh.setToolTip("Refresh audio devices")
        btn_refresh.setFixedSize(32, 30)
        btn_refresh.clicked.connect(self.refresh_devices)
        mon_row.addWidget(btn_refresh)
        dev_container.addLayout(mon_row)

        # Microfone (Sua voz)
        lbl_mic = QLabel("🎤 Microphone (Your Voice):")
        lbl_mic.setObjectName("lbl_field_header")
        dev_container.addWidget(lbl_mic)

        self.combo_mic = QComboBox()
        self.combo_mic.currentIndexChanged.connect(self._on_mic_changed)
        dev_container.addWidget(self.combo_mic)

        # Seletores Rápidos de Idioma (Entrada / Saída)
        lang_box = QHBoxLayout()
        lang_box.setSpacing(8)

        v_in = QVBoxLayout()
        v_in.setSpacing(4)
        lbl_in = QLabel("🗣️ Spoken Language:")
        lbl_in.setObjectName("lbl_field_header")
        self.combo_input_lang = QComboBox()
        for code, label in INPUT_LANGUAGES:
            self.combo_input_lang.addItem(label, code)
        self.combo_input_lang.currentIndexChanged.connect(self._on_input_lang_changed)
        v_in.addWidget(lbl_in)
        v_in.addWidget(self.combo_input_lang)
        lang_box.addLayout(v_in, 1)

        v_out = QVBoxLayout()
        v_out.setSpacing(4)
        lbl_out = QLabel("📋 Summary Output:")
        lbl_out.setObjectName("lbl_field_header")
        self.combo_output_lang = QComboBox()
        for code, label in OUTPUT_LANGUAGES:
            self.combo_output_lang.addItem(label, code)
        self.combo_output_lang.currentIndexChanged.connect(self._on_output_lang_changed)
        v_out.addWidget(lbl_out)
        v_out.addWidget(self.combo_output_lang)
        lang_box.addLayout(v_out, 1)

        dev_container.addLayout(lang_box)

        layout.addLayout(dev_container)

    def refresh_devices(self):
        self.combo_monitor.blockSignals(True)
        self.combo_mic.blockSignals(True)

        self.combo_monitor.clear()
        self.combo_mic.clear()

        self.combo_monitor.addItem("Auto (Default Output)", "auto")
        self.combo_mic.addItem("Auto (Default Microphone)", "auto")

        saved_monitor = config.get("selected_monitor", "auto")
        saved_mic = config.get("selected_mic", "auto")

        sinks = list_sinks()
        sel_mon_idx = 0
        for idx, s in enumerate(sinks, start=1):
            name = s["monitor_name"]
            desc = s["description"]
            if s["is_default"]:
                desc += " ★"
            self.combo_monitor.addItem(desc, name)
            if saved_monitor == name:
                sel_mon_idx = idx

        mics = list_microphones()
        sel_mic_idx = 0
        for idx, m in enumerate(mics, start=1):
            name = m["name"]
            desc = m["description"]
            if m["is_default"]:
                desc += " ★"
            self.combo_mic.addItem(desc, name)
            if saved_mic == name:
                sel_mic_idx = idx

        self.combo_monitor.setCurrentIndex(sel_mon_idx)
        self.combo_mic.setCurrentIndex(sel_mic_idx)

        self.combo_monitor.blockSignals(False)
        self.combo_mic.blockSignals(False)

    def refresh_languages(self):
        self.combo_input_lang.blockSignals(True)
        self.combo_output_lang.blockSignals(True)

        saved_in = config.get("input_language", "auto")
        saved_out = config.get("output_language", "pt")

        idx_in = self.combo_input_lang.findData(saved_in)
        if idx_in >= 0:
            self.combo_input_lang.setCurrentIndex(idx_in)

        idx_out = self.combo_output_lang.findData(saved_out)
        if idx_out >= 0:
            self.combo_output_lang.setCurrentIndex(idx_out)

        self.combo_input_lang.blockSignals(False)
        self.combo_output_lang.blockSignals(False)

    def _on_monitor_changed(self, index: int):
        val = self.combo_monitor.currentData()
        config.set("selected_monitor", val)
        self.devices_changed.emit()

    def _on_mic_changed(self, index: int):
        val = self.combo_mic.currentData()
        config.set("selected_mic", val)
        self.devices_changed.emit()

    def _on_input_lang_changed(self, index: int):
        val = self.combo_input_lang.currentData()
        config.set("input_language", val)
        self.languages_changed.emit()

    def _on_output_lang_changed(self, index: int):
        val = self.combo_output_lang.currentData()
        config.set("output_language", val)
        self.languages_changed.emit()

    def _toggle_recording(self):
        if self.btn_record.objectName() == "btn_record_start":
            self.start_requested.emit()
        else:
            self.lbl_timer.setText("00:00:00")
            self.stop_requested.emit()

    def set_recording_state(self, is_recording: bool):
        if is_recording:
            self.btn_record.setObjectName("btn_record_stop")
            self.btn_record.setText("⏹ Stop & Summarize")
            self.lbl_status_badge.setText("🔴 RECORDING")
            self.lbl_status_badge.setStyleSheet(
                "color: #ed8796; background-color: rgba(237, 135, 150, 0.2); "
                "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
            )
            self.lbl_timer.setObjectName("lbl_timer_recording")
            self.combo_monitor.setEnabled(False)
            self.combo_mic.setEnabled(False)
            self.combo_input_lang.setEnabled(False)
            self.combo_output_lang.setEnabled(False)
        else:
            self.btn_record.setObjectName("btn_record_start")
            self.btn_record.setText("▶ Start Recording")
            self.lbl_status_badge.setText("● READY")
            self.lbl_status_badge.setStyleSheet(
                "color: #a6da95; background-color: rgba(166, 218, 149, 0.15); "
                "border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;"
            )
            self.lbl_timer.setObjectName("lbl_timer_idle")
            # RESET DO TIMER AO PARAR A GRAVAÇÃO
            self.lbl_timer.setText("00:00:00")
            self.combo_monitor.setEnabled(True)
            self.combo_mic.setEnabled(True)
            self.combo_input_lang.setEnabled(True)
            self.combo_output_lang.setEnabled(True)

        self.lbl_timer.style().unpolish(self.lbl_timer)
        self.lbl_timer.style().polish(self.lbl_timer)
        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)

    def update_timer(self, seconds: int):
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        self.lbl_timer.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
