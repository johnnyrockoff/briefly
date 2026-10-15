import json
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, List

from app.config import config


def check_ffmpeg() -> Dict[str, Any]:
    path = shutil.which("ffmpeg")
    if not path:
        return {
            "name": "FFmpeg Audio Engine",
            "status": "error",
            "installed": False,
            "title": "FFmpeg is not installed",
            "message": "FFmpeg is required to record and mix computer and microphone audio.",
            "action": "Install via terminal: sudo apt install ffmpeg (Ubuntu/Debian) or sudo dnf install ffmpeg (Fedora)",
        }
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=2)
        version_line = res.stdout.splitlines()[0] if res.stdout else "Installed"
        return {
            "name": "FFmpeg Audio Engine",
            "status": "ok",
            "installed": True,
            "title": "FFmpeg Installed",
            "message": version_line,
            "action": None,
        }
    except Exception as e:
        return {
            "name": "FFmpeg Audio Engine",
            "status": "ok",
            "installed": True,
            "title": "FFmpeg Installed",
            "message": f"Found at {path}",
            "action": None,
        }


def check_audio_server() -> Dict[str, Any]:
    path = shutil.which("pactl")
    if not path:
        return {
            "name": "Audio Server (PulseAudio / PipeWire)",
            "status": "error",
            "installed": False,
            "title": "pactl utility not found",
            "message": "pactl is required to detect system playback and microphone streams.",
            "action": "Install pulseaudio-utils or pipewire-bin",
        }
    try:
        from app.audio.devices import get_default_sink, get_default_source, list_microphones, list_sinks

        sink = get_default_sink()
        source = get_default_source()
        sinks_count = len(list_sinks())
        mics_count = len(list_microphones())

        if not sink and not source:
            return {
                "name": "Audio Server (PulseAudio / PipeWire)",
                "status": "warning",
                "installed": True,
                "title": "No audio devices active",
                "message": "Audio server is running but no active sink or source was detected.",
                "action": "Check your sound settings or plug in a microphone/headphones.",
            }

        return {
            "name": "Audio Server (PulseAudio / PipeWire)",
            "status": "ok",
            "installed": True,
            "title": "Audio Server Connected",
            "message": f"{sinks_count} output(s) and {mics_count} microphone(s) detected.",
            "action": None,
        }
    except Exception as e:
        return {
            "name": "Audio Server (PulseAudio / PipeWire)",
            "status": "warning",
            "installed": True,
            "title": "Audio Server Warning",
            "message": str(e),
            "action": None,
        }


def check_whisper_engine() -> Dict[str, Any]:
    try:
        import torch
        import whisper

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return {
                "name": "Whisper AI Engine",
                "status": "ok",
                "installed": True,
                "title": "Whisper Ready (GPU Accelerated)",
                "message": f"Using NVIDIA CUDA: {gpu_name}",
                "action": None,
            }
        else:
            return {
                "name": "Whisper AI Engine",
                "status": "ok",
                "installed": True,
                "title": "Whisper Ready (CPU Mode)",
                "message": "Running on CPU (CUDA GPU not detected or driver not loaded).",
                "action": "Optional: Install NVIDIA drivers & CUDA toolkit for faster transcription.",
            }
    except ImportError as e:
        return {
            "name": "Whisper AI Engine",
            "status": "error",
            "installed": False,
            "title": "Whisper or PyTorch Missing",
            "message": str(e),
            "action": "Install requirements: pip install openai-whisper torch",
        }


def check_ollama_service() -> Dict[str, Any]:
    url = config.get("ollama_tags_url", "http://localhost:11434/api/tags")
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            configured_model = config.get("ollama_model", "qwen2.5:7b")

            if not models:
                return {
                    "name": "Ollama Local AI",
                    "status": "warning",
                    "installed": True,
                    "title": "Ollama Running (No Models Found)",
                    "message": "Ollama service is active, but no models are currently downloaded.",
                    "action": f"Run in terminal: ollama run {configured_model}",
                }

            has_target = any(configured_model in m for m in models)
            msg = f"{len(models)} model(s) available: {', '.join(models[:3])}"
            if len(models) > 3:
                msg += "..."

            if not has_target:
                return {
                    "name": "Ollama Local AI",
                    "status": "warning",
                    "installed": True,
                    "title": f"Configured model '{configured_model}' not found",
                    "message": msg,
                    "action": f"Run in terminal: ollama run {configured_model} (or select an existing model in Settings)",
                }

            return {
                "name": "Ollama Local AI",
                "status": "ok",
                "installed": True,
                "title": "Ollama Connected & Ready",
                "message": msg,
                "action": None,
            }
    except Exception:
        configured_model = config.get("ollama_model", "qwen2.5:7b")
        return {
            "name": "Ollama Local AI",
            "status": "warning",
            "installed": False,
            "title": "Ollama Not Running",
            "message": "Cannot reach Ollama at http://localhost:11434. Meeting summaries require Ollama.",
            "action": f"Start it with: ollama serve\nOr install Ollama from https://ollama.ai and run: ollama run {configured_model}",
        }


def run_full_system_check() -> Dict[str, Any]:
    items = [
        check_ffmpeg(),
        check_audio_server(),
        check_whisper_engine(),
        check_ollama_service(),
    ]

    has_error = any(item["status"] == "error" for item in items)
    has_warning = any(item["status"] == "warning" for item in items)

    if has_error:
        overall = "error"
    elif has_warning:
        overall = "warning"
    else:
        overall = "ok"

    return {
        "overall": overall,
        "items": items,
    }
