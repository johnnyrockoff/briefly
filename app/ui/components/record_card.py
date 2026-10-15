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


class RecordCard(QFrame):
    start_requested = Signal()
    stop_requested = Signal()
    devices_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        self._init_ui()
        self.refresh_devices()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Header com título e status
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("Meeting Recording Control")
        self.lbl_title.setObjectName("lbl_card_title")
        top_bar.addWidget(self.lbl_title)

        self.lbl_status_badge = QLabel("● READY")
        self.lbl_status_badge.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_status_badge)
        layout.addLayout(top_bar)

        # Timer Display
        timer_box = QHBoxLayout()
        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setObjectName("lbl_timer")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_box.addWidget(self.lbl_timer)
        layout.addLayout(timer_box)

        # Botão Principal Gravar / Parar
        btn_box = QHBoxLayout()
        self.btn_record = QPushButton("▶ Start Meeting Recording")
        self.btn_record.setObjectName("btn_record_start")
        self.btn_record.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_record.clicked.connect(self._toggle_recording)
        btn_box.addWidget(self.btn_record)
        layout.addLayout(btn_box)

        # Dispositivos de Áudio (Áudio do Sistema + Microfone)
        dev_layout = QHBoxLayout()

        # Monitor (Áudio do PC)
        monitor_col = QVBoxLayout()
        lbl_mon = QLabel("🔊 System Audio (Meeting / Headphones):")
        lbl_mon.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.combo_monitor = QComboBox()
        self.combo_monitor.currentIndexChanged.connect(self._on_monitor_changed)
        monitor_col.addWidget(lbl_mon)
        monitor_col.addWidget(self.combo_monitor)
        dev_layout.addLayout(monitor_col, 1)

        # Microfone
        mic_col = QVBoxLayout()
        lbl_mic = QLabel("🎤 Microphone (Your Voice):")
        lbl_mic.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.combo_mic = QComboBox()
        self.combo_mic.currentIndexChanged.connect(self._on_mic_changed)
        mic_col.addWidget(lbl_mic)
        mic_col.addWidget(self.combo_mic)
        dev_layout.addLayout(mic_col, 1)

        # Botão Atualizar Dispositivos
        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Refresh connected audio devices")
        btn_refresh.setFixedWidth(36)
        btn_refresh.clicked.connect(self.refresh_devices)
        dev_layout.addWidget(btn_refresh, 0, Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(dev_layout)

    def refresh_devices(self):
        # Bloquear sinais para não salvar durante recarga
        self.combo_monitor.blockSignals(True)
        self.combo_mic.blockSignals(True)

        self.combo_monitor.clear()
        self.combo_mic.clear()

        # Opção automática default
        def_sink = get_default_sink()
        def_source = get_default_source()

        self.combo_monitor.addItem("Automatic (System default output)", "auto")
        self.combo_mic.addItem("Automatic (System default microphone)", "auto")

        saved_monitor = config.get("selected_monitor", "auto")
        saved_mic = config.get("selected_mic", "auto")

        # Preencher sinks
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

        # Preencher microfones
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

    def _on_monitor_changed(self, index: int):
        val = self.combo_monitor.currentData()
        config.set("selected_monitor", val)
        self.devices_changed.emit()

    def _on_mic_changed(self, index: int):
        val = self.combo_mic.currentData()
        config.set("selected_mic", val)
        self.devices_changed.emit()

    def _toggle_recording(self):
        if self.btn_record.objectName() == "btn_record_start":
            self.start_requested.emit()
        else:
            self.stop_requested.emit()

    def set_recording_state(self, is_recording: bool):
        if is_recording:
            self.btn_record.setObjectName("btn_record_stop")
            self.btn_record.setText("⏹ Stop Recording & Process")
            self.lbl_status_badge.setText("🔴 RECORDING MEETING")
            self.lbl_status_badge.setStyleSheet("color: #f38ba8; font-weight: bold;")
            self.combo_monitor.setEnabled(False)
            self.combo_mic.setEnabled(False)
        else:
            self.btn_record.setObjectName("btn_record_start")
            self.btn_record.setText("▶ Start Meeting Recording")
            self.lbl_status_badge.setText("● READY")
            self.lbl_status_badge.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.combo_monitor.setEnabled(True)
            self.combo_mic.setEnabled(True)

        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)

    def update_timer(self, seconds: int):
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        self.lbl_timer.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
