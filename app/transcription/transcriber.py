import gc
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.config import config, get_transcripts_dir


class TranscriptionWorker(QObject):
    progress = Signal(str)
    finished = Signal(str, str)  # wav_path, txt_path
    error = Signal(str)

    def __init__(self, wav_path: str, model_name: Optional[str] = None, device: Optional[str] = None):
        super().__init__()
        self.wav_path = Path(wav_path)
        self.model_name = model_name or config.get("whisper_model", "turbo")
        self.device = device or config.get("whisper_device", "cuda")

    def run(self):
        try:
            if not self.wav_path.exists():
                self.error.emit(f"Audio file not found: {self.wav_path}")
                return

            self.progress.emit(f"Loading Whisper ({self.model_name}) on {self.device}...")
            import torch
            import whisper

            # Se cuda foi requisitado mas não disponível, fallback para cpu
            target_device = self.device
            if target_device == "cuda" and not torch.cuda.is_available():
                self.progress.emit("CUDA not available. Using CPU for Whisper...")
                target_device = "cpu"

            model = whisper.load_model(self.model_name, device=target_device)

            from app.languages import get_transcription_initial_prompt

            lang = config.get("input_language", "auto")
            initial_prompt = get_transcription_initial_prompt(lang)

            kwargs = {
                "verbose": False,
                "beam_size": 5,
                "best_of": 5,
                "temperature": (0.0, 0.2),
                "condition_on_previous_text": False,
                "compression_ratio_threshold": 2.4,
                "no_speech_threshold": 0.6,
                "initial_prompt": initial_prompt,
                "fp16": (target_device == "cuda"),
            }
            if lang and lang != "auto":
                kwargs["language"] = lang

            lang_label = lang.upper() if lang != "auto" else "Auto-detect"
            self.progress.emit(f"Transcribing {self.wav_path.name} (Model: {self.model_name}, Spoken: {lang_label})...")
            result = model.transcribe(str(self.wav_path), **kwargs)

            t_dir = get_transcripts_dir()
            t_dir.mkdir(parents=True, exist_ok=True)
            txt_path = t_dir / f"{self.wav_path.stem}.txt"
            txt_path.write_text(result["text"].strip(), encoding="utf-8")

            # Salva também vtt/srt se o usuário quiser detalhes temporais futuramente
            try:
                from whisper.utils import get_writer
                writer = get_writer("vtt", str(t_dir))
                writer(result, str(self.wav_path))
            except Exception:
                pass

            # Libera memória GPU/RAM
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

            self.progress.emit("Transcription completed successfully.")
            self.finished.emit(str(self.wav_path), str(txt_path))

        except Exception as e:
            self.error.emit(f"Transcription error: {e}")


class TranscriberManager(QObject):
    progress = Signal(str)
    finished = Signal(str, str)
    error = Signal(str)
    is_busy = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[TranscriptionWorker] = None

    def start_transcription(self, wav_path: str, model_name: Optional[str] = None):
        if self._thread and self._thread.isRunning():
            self.error.emit("A transcription is already in progress.")
            return

        self.is_busy.emit(True)
        self._thread = QThread()
        self._worker = TranscriptionWorker(wav_path, model_name=model_name)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._thread.start()

    def _on_finished(self, wav_path: str, txt_path: str):
        self._cleanup()
        self.is_busy.emit(False)
        self.finished.emit(wav_path, txt_path)

    def _on_error(self, err_msg: str):
        self._cleanup()
        self.is_busy.emit(False)
        self.error.emit(err_msg)

    def _cleanup(self):
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
