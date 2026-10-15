import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.config import LOCAL_BIN_DIR, config


class InstallWorker(QThread):
    progress = Signal(int, str)      # (percentage, status_text)
    finished = Signal(bool, str)     # (success, message)

    def __init__(self, task_type: str, payload: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.payload = payload
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self.task_type == "ffmpeg":
                self._install_ffmpeg()
            elif self.task_type == "ollama_model":
                self._pull_ollama_model(self.payload or config.get("ollama_model", "qwen2.5:7b"))
            elif self.task_type == "ollama_service":
                self._install_ollama_service()
            else:
                self.finished.emit(False, f"Unknown install task: {self.task_type}")
        except Exception as e:
            self.finished.emit(False, str(e))

    def _download_with_progress(self, url: str, dest_path: Path, label: str):
        req = urllib.request.Request(url, headers={"User-Agent": "Briefly-Installer/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024

            while not self._is_cancelled:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = int(downloaded / total_size * 100)
                    mb_cur = downloaded / (1024 * 1024)
                    mb_tot = total_size / (1024 * 1024)
                    self.progress.emit(pct, f"Downloading {label}: {pct}% ({mb_cur:.1f} MB / {mb_tot:.1f} MB)")
                else:
                    mb_cur = downloaded / (1024 * 1024)
                    self.progress.emit(50, f"Downloading {label}: {mb_cur:.1f} MB")

    def _install_ffmpeg(self):
        LOCAL_BIN_DIR.mkdir(parents=True, exist_ok=True)
        self.progress.emit(5, "Connecting to official FFmpeg archive...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            if sys.platform == "win32":
                # Windows 64-bit portable essentials
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                archive_file = tmp_path / "ffmpeg.zip"
                self._download_with_progress(url, archive_file, "FFmpeg for Windows")

                self.progress.emit(90, "Extracting ffmpeg.exe to Briefly bin folder...")
                with zipfile.ZipFile(archive_file, "r") as z:
                    for member in z.namelist():
                        if member.lower().endswith("bin/ffmpeg.exe") or member.lower().endswith("ffmpeg.exe"):
                            target_exe = LOCAL_BIN_DIR / "ffmpeg.exe"
                            with z.open(member) as source, open(target_exe, "wb") as dest:
                                shutil.copyfileobj(source, dest)
                            break
            else:
                # Linux x86_64 static build
                url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
                archive_file = tmp_path / "ffmpeg.tar.xz"
                self._download_with_progress(url, archive_file, "FFmpeg for Linux")

                self.progress.emit(90, "Extracting ffmpeg binary to Briefly bin folder...")
                with tarfile.open(archive_file, "r:xz") as tar:
                    for member in tar.getmembers():
                        if member.name.endswith("/ffmpeg") or member.name == "ffmpeg":
                            target_bin = LOCAL_BIN_DIR / "ffmpeg"
                            f = tar.extractfile(member)
                            if f:
                                with open(target_bin, "wb") as dest:
                                    shutil.copyfileobj(f, dest)
                                # Make executable
                                target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                            break

        # Verify installation
        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            self.progress.emit(100, "FFmpeg installed successfully!")
            self.finished.emit(True, f"FFmpeg ready at {ffmpeg_bin}")
        else:
            self.finished.emit(False, "FFmpeg extraction finished but binary was not found in PATH.")

    def _pull_ollama_model(self, model_name: str):
        self.progress.emit(5, f"Requesting {model_name} from Ollama library...")
        url = "http://localhost:11434/api/pull"
        data = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        with urllib.request.urlopen(req, timeout=300) as response:
            for line in response:
                if self._is_cancelled:
                    break
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    payload = json.loads(line_str)
                    status = payload.get("status", "")
                    total = payload.get("total", 0)
                    completed = payload.get("completed", 0)

                    if total > 0 and completed > 0:
                        pct = int(completed / total * 100)
                        mb_c = completed / (1024 * 1024)
                        mb_t = total / (1024 * 1024)
                        self.progress.emit(pct, f"{status}: {pct}% ({mb_c:.0f} MB / {mb_t:.0f} MB)")
                    elif status:
                        self.progress.emit(50, f"{status}...")
                except Exception:
                    pass

        self.progress.emit(100, f"Model {model_name} ready!")
        self.finished.emit(True, f"Ollama model {model_name} downloaded successfully.")

    def _install_ollama_service(self):
        if sys.platform == "win32":
            self.progress.emit(10, "Downloading official Ollama Windows installer...")
            with tempfile.TemporaryDirectory() as tmp_dir:
                dest = Path(tmp_dir) / "OllamaSetup.exe"
                url = "https://ollama.com/download/OllamaSetup.exe"
                self._download_with_progress(url, dest, "Ollama Installer")
                self.progress.emit(90, "Launching Ollama installer...")
                subprocess.Popen([str(dest)])
                self.progress.emit(100, "Installer started. Follow setup wizard.")
                self.finished.emit(True, "Ollama installer launched.")
        else:
            self.progress.emit(10, "Running Ollama installation script...")
            # On Linux, instructions or pkexec command
            cmd = "curl -fsSL https://ollama.com/install.sh | sh"
            if shutil.which("pkexec"):
                subprocess.Popen(["pkexec", "bash", "-c", cmd])
                self.finished.emit(True, "Installation prompt opened in terminal.")
            else:
                self.finished.emit(False, "Please install Ollama by running in terminal: curl -fsSL https://ollama.com/install.sh | sh")


class DependencyInstaller(QObject):
    """Facade for managing automated dependency installs with live Qt UI progress."""
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[InstallWorker] = None

    @property
    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def start_install(self, task_type: str, payload: Optional[str] = None):
        if self.is_busy:
            return
        self._worker = InstallWorker(task_type, payload, self)
        self._worker.progress.connect(self.progress.emit)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self, success: bool, msg: str):
        self.finished.emit(success, msg)
        self._worker = None
