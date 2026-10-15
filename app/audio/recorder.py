import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from app.audio.devices import resolve_recording_devices
from app.config import RECORDINGS_DIR, config


class AudioRecorder(QObject):
    """
    Manages background audio recording of system monitor (call participants)
    and user microphone using FFmpeg.
    """
    state_changed = Signal(bool)          # True when recording starts, False when stops
    tick = Signal(int)                   # Elapsed seconds
    finished = Signal(str)               # Emitted with generated .wav path
    error = Signal(str)                  # Emitted on error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process: Optional[subprocess.Popen] = None
        self._current_wav: Optional[Path] = None
        self._start_time: float = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)

    @property
    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start_recording(self) -> bool:
        if self.is_recording:
            return False

        monitor, mic = resolve_recording_devices(
            config.get("selected_monitor", "auto"),
            config.get("selected_mic", "auto")
        )

        if not monitor and not mic:
            self.error.emit("No audio devices (microphone or system output) were found.")
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self._current_wav = RECORDINGS_DIR / f"reuniao_{timestamp}.wav"
        log_file = RECORDINGS_DIR / f"reuniao_{timestamp}.log"

        cmd = [
            "ffmpeg", "-hide_banner", "-nostdin", "-y",
        ]

        if monitor and mic:
            # Ambos disponíveis: mixar 2 inputs
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", "pulse", "-i", monitor,
                "-thread_queue_size", "2048",
                "-f", "pulse", "-i", mic,
                "-filter_complex",
                "[0:a]aresample=16000,aformat=channel_layouts=mono[out];"
                "[1:a]aresample=16000,aformat=channel_layouts=mono[mic];"
                "[out][mic]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0,alimiter=limit=0.95[mix]",
                "-map", "[mix]",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(self._current_wav)
            ])
        elif monitor:
            # Apenas áudio do computador
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", "pulse", "-i", monitor,
                "-af", "aresample=16000,aformat=channel_layouts=mono",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(self._current_wav)
            ])
        else:
            # Apenas microfone
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", "pulse", "-i", mic,
                "-af", "aresample=16000,aformat=channel_layouts=mono",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(self._current_wav)
            ])

        try:
            self._log_handle = open(log_file, "w", encoding="utf-8")
            # Iniciar processo com grupo de processo próprio para manipulação segura de sinais
            self._process = subprocess.Popen(
                cmd,
                stdout=self._log_handle,
                stderr=self._log_handle,
                preexec_fn=os.setsid,
            )
        except Exception as e:
            self.error.emit(f"Failed to start FFmpeg: {e}")
            return False

        # Verifica se o processo permaneceu vivo por 1 segundo
        time.sleep(1.0)
        if self._process.poll() is not None:
            self.error.emit(f"FFmpeg exited unexpectedly. Check logs at {log_file}")
            self._process = None
            return False

        self._start_time = time.time()
        self._timer.start()
        self.state_changed.emit(True)
        self.tick.emit(0)
        return True

    def stop_recording(self) -> None:
        if not self.is_recording or not self._process:
            return

        self._timer.stop()
        proc = self._process
        self._process = None

        try:
            # Envia SIGINT para o grupo de processo (equivalente ao Ctrl+C limpo para fechar WAV)
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        except ProcessLookupError:
            pass

        # Aguarda finalização limpa do processo
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
            except Exception:
                pass

        if hasattr(self, "_log_handle") and self._log_handle and not self._log_handle.closed:
            self._log_handle.close()

        self.state_changed.emit(False)

        if self._current_wav and self._current_wav.exists() and self._current_wav.stat().st_size > 44:
            self.finished.emit(str(self._current_wav))
        else:
            self.error.emit("Recording finished, but the audio file is empty or corrupted.")

    def _on_timer_tick(self) -> None:
        if self.is_recording:
            elapsed = int(time.time() - self._start_time)
            self.tick.emit(elapsed)
