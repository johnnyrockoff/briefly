import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.config import SUMMARIES_DIR, config, get_effective_system_prompt


def get_available_ollama_models(ollama_tags_url: Optional[str] = None) -> List[str]:
    url = ollama_tags_url or config.get("ollama_tags_url", "http://localhost:11434/api/tags")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return models
    except Exception:
        return ["qwen2.5:7b"]


class SummarizerWorker(QObject):
    progress = Signal(str)
    chunk_received = Signal(str)
    finished = Signal(str, str, str)  # txt_path, md_path, summary_content
    error = Signal(str)

    def __init__(self, txt_path: str, model_name: Optional[str] = None):
        super().__init__()
        self.txt_path = Path(txt_path)
        self.model_name = model_name or config.get("ollama_model", "qwen2.5:7b")
        self.api_url = config.get("ollama_url", "http://localhost:11434/api/chat")
        self.system_prompt = get_effective_system_prompt()
        self.keep_alive = config.get("keep_alive_ollama", 0)
        self.temperature = float(config.get("temperature", 0.2))
        self.num_ctx = int(config.get("num_ctx", 8192))

    def run(self):
        try:
            if not self.txt_path.exists():
                self.error.emit(f"Transcript file not found: {self.txt_path}")
                return

            transcript = self.txt_path.read_text(encoding="utf-8").strip()
            if not transcript:
                self.error.emit("Transcript is empty; no summary could be generated.")
                return

            self.progress.emit(f"Sending transcript to Ollama ({self.model_name})...")

            payload = {
                "model": self.model_name,
                "stream": True,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Summarize this meeting transcript from {self.txt_path.name}.\n"
                            f"<transcript>\n{transcript}\n</transcript>"
                        ),
                    },
                ],
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
                "keep_alive": self.keep_alive,
            }

            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            accumulated_chunks = []
            with urllib.request.urlopen(req, timeout=600) as response:
                for line in response:
                    if not line:
                        continue
                    try:
                        chunk_obj = json.loads(line.decode("utf-8"))
                        msg_piece = chunk_obj.get("message", {}).get("content", "")
                        if msg_piece:
                            accumulated_chunks.append(msg_piece)
                            self.chunk_received.emit(msg_piece)
                    except Exception:
                        continue

            summary = "".join(accumulated_chunks).strip()
            if not summary:
                self.error.emit("Ollama returned an empty response.")
                return

            SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
            output_path = SUMMARIES_DIR / f"{self.txt_path.stem}.md"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            document = (
                f"<!-- Source: {self.txt_path.name} -->\n"
                f"<!-- Generated locally with {self.model_name} at {now_str} -->\n\n"
                f"{summary}\n"
            )
            output_path.write_text(document, encoding="utf-8")

            self.progress.emit(f"Summary saved successfully to {output_path.name}")
            self.finished.emit(str(self.txt_path), str(output_path), summary)

        except urllib.error.URLError as e:
            self.error.emit(f"Failed to connect to Ollama ({self.api_url}): Check if service is running. {e}")
        except Exception as e:
            self.error.emit(f"Error generating summary: {e}")


class SummarizerManager(QObject):
    progress = Signal(str)
    chunk_received = Signal(str)
    finished = Signal(str, str, str)
    error = Signal(str)
    is_busy = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[SummarizerWorker] = None

    def start_summarization(self, txt_path: str, model_name: Optional[str] = None):
        if self._thread and self._thread.isRunning():
            self.error.emit("A summary is already being generated.")
            return

        self.is_busy.emit(True)
        self._thread = QThread()
        self._worker = SummarizerWorker(txt_path, model_name=model_name)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress.emit)
        self._worker.chunk_received.connect(self.chunk_received.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._thread.start()

    def _on_finished(self, txt_path: str, md_path: str, content: str):
        self._cleanup()
        self.is_busy.emit(False)
        self.finished.emit(txt_path, md_path, content)

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
