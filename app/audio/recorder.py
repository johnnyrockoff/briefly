import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from app.audio.devices import resolve_recording_devices
from app.config import config, get_recordings_dir


class AudioRecorder(QObject):
    """
    Manages background audio recording of system monitor (call participants)
    and user microphone using FFmpeg across Linux (Pulse/PipeWire) and Windows (WASAPI).
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
        rec_dir = get_recordings_dir()
        rec_dir.mkdir(parents=True, exist_ok=True)
        self._current_wav = rec_dir / f"reuniao_{timestamp}.wav"
        log_file = rec_dir / f"reuniao_{timestamp}.log"

        cmd = [
            "ffmpeg", "-hide_banner", "-nostdin", "-y",
        ]

        audio_format = "wasapi" if sys.platform == "win32" else "pulse"

        if monitor and mic:
            # Both available: mix 2 inputs
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", audio_format, "-i", monitor,
                "-thread_queue_size", "2048",
                "-f", audio_format, "-i", mic,
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
            # System audio only
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", audio_format, "-i", monitor,
                "-af", "aresample=16000,aformat=channel_layouts=mono",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(self._current_wav)
            ])
        else:
            # Microphone only
            cmd.extend([
                "-thread_queue_size", "2048",
                "-f", audio_format, "-i", mic,
                "-af", "aresample=16000,aformat=channel_layouts=mono",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(self._current_wav)
            ])

        try:
            self._log_handle = open(log_file, "w", encoding="utf-8")
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            preexec_fn = os.setsid if sys.platform != "win32" else None

            self._process = subprocess.Popen(
                cmd,
                stdout=self._log_handle,
                stderr=self._log_handle,
                preexec_fn=preexec_fn,
                creationflags=creationflags,
            )
        except Exception as e:
            self.error.emit(f"Failed to start FFmpeg: {e}")
            return False

        # Verify process stayed alive
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

        if sys.platform == "win32":
            ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
            if ctrl_break is not None:
                try:
                    proc.send_signal(ctrl_break)
                except Exception:
                    proc.terminate()
            else:
                proc.terminate()
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            except ProcessLookupError:
                pass

        # Wait for clean process finalization
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                proc.terminate()
            else:
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
