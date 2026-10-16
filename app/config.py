import json
import os
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent

def _resolve_default_storage() -> Path:
    local_rec = BASE_DIR / "recordings"
    if local_rec.exists() and os.access(BASE_DIR, os.W_OK):
        return BASE_DIR
    docs_dir = Path.home() / "Documents" / "Briefly"
    if not (Path.home() / "Documents").exists():
        docs_dir = Path.home() / "Briefly"
    # Backward compatibility with existing user data
    legacy_docs = Path.home() / "Documents" / "MeetingNotes"
    if legacy_docs.exists() and not docs_dir.exists():
        return legacy_docs
    return docs_dir

def get_storage_base() -> Path:
    """Returns the root directory where meeting data is stored."""
    try:
        if "config" in globals():
            custom = config.get("storage_dir", "")
            if custom and str(custom).strip():
                return Path(str(custom).strip()).expanduser().resolve()
    except Exception:
        pass
    return _resolve_default_storage()

def get_recordings_dir() -> Path:
    return get_storage_base() / "recordings"

def get_transcripts_dir() -> Path:
    return get_storage_base() / "transcripts"

def get_summaries_dir() -> Path:
    return get_storage_base() / "summaries"

def init_storage() -> None:
    """Ensures storage directory and its subfolders exist."""
    get_storage_base().mkdir(parents=True, exist_ok=True)
    get_recordings_dir().mkdir(parents=True, exist_ok=True)
    get_transcripts_dir().mkdir(parents=True, exist_ok=True)
    get_summaries_dir().mkdir(parents=True, exist_ok=True)

STORAGE_BASE = _resolve_default_storage()
RECORDINGS_DIR = get_recordings_dir()
TRANSCRIPTS_DIR = get_transcripts_dir()
SUMMARIES_DIR = get_summaries_dir()

def sync_storage_globals() -> None:
    global STORAGE_BASE, RECORDINGS_DIR, TRANSCRIPTS_DIR, SUMMARIES_DIR
    STORAGE_BASE = get_storage_base()
    RECORDINGS_DIR = get_recordings_dir()
    TRANSCRIPTS_DIR = get_transcripts_dir()
    SUMMARIES_DIR = get_summaries_dir()
    init_storage()

import sys

if sys.platform == "win32":
    appdata = os.getenv("APPDATA")
    CONFIG_DIR = Path(appdata) / "Briefly" if appdata else Path.home() / "AppData" / "Roaming" / "Briefly"
    local_appdata = os.getenv("LOCALAPPDATA")
    LOCAL_BIN_DIR = (Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local") / "Briefly" / "bin"
else:
    CONFIG_DIR = Path.home() / ".config" / "briefly"
    LOCAL_BIN_DIR = Path.home() / ".local" / "share" / "briefly" / "bin"

MODELS_DIR = LOCAL_BIN_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_BIN_DIR.mkdir(parents=True, exist_ok=True)
str_bin = str(LOCAL_BIN_DIR)
if str_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str_bin + os.pathsep + os.environ.get("PATH", "")

LEGACY_CONFIG_FILE = Path.home() / ".config" / "meeting-notes" / "config.json"
CONFIG_FILE = CONFIG_DIR / "config.json"

from app.languages import (
    LEGACY_PROMPT_SIGNATURES,
    PROMPTS_BY_LANGUAGE,
    get_prompt_for_language,
)

DEFAULT_SYSTEM_PROMPT = PROMPTS_BY_LANGUAGE["pt"]

DEFAULT_CONFIG: Dict[str, Any] = {
    "storage_dir": "",            # Custom storage location (empty = default ~/Documents/Briefly)
    "whisper_model": "turbo",
    "whisper_device": "cuda",
    "input_language": "auto",       # Spoken language: 'auto', 'pt', 'en', 'es', etc.
    "output_language": "pt",      # Summary output language: 'pt', 'en', 'es', etc.
    "enable_diarization": True,    # Neural speaker diarization (Interlocutor 1, 2...)
    "ollama_url": "http://localhost:11434/api/chat",
    "ollama_tags_url": "http://localhost:11434/api/tags",
    "ollama_model": "qwen2.5:7b",
    "selected_monitor": "auto",  # 'auto' or sink monitor name
    "selected_mic": "auto",      # 'auto' or source name
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "auto_transcribe": True,
    "auto_summarize": True,
    "minimize_to_tray_on_close": True,
    "keep_alive_ollama": 0,
    "num_ctx": 8192,
    "temperature": 0.2,
}


def get_effective_system_prompt() -> str:
    """Returns the effective system prompt based on user customization or selected output language."""
    saved_prompt = config.get("system_prompt", "").strip()
    out_lang = config.get("output_language", "pt")
    default_for_lang = get_prompt_for_language(out_lang).strip()

    # If user hasn't customized the prompt, or it matches any standard prompt,
    # or it is an old legacy mixed prompt, use the clean target language prompt
    if (
        not saved_prompt
        or any(saved_prompt == p.strip() for p in PROMPTS_BY_LANGUAGE.values())
        or any(sig in saved_prompt for sig in LEGACY_PROMPT_SIGNATURES)
    ):
        return default_for_lang

    return saved_prompt


class ConfigManager:
    """Manages application configuration, persisting to ~/.config/briefly/config.json."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()
        init_storage()

    def load(self) -> None:
        target = CONFIG_FILE if CONFIG_FILE.exists() else (LEGACY_CONFIG_FILE if LEGACY_CONFIG_FILE.exists() else None)
        if target and target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"Error loading configuration: {e}")

        # Automatic migration from legacy mixed prompts
        cur_p = self.data.get("system_prompt", "")
        if cur_p and any(sig in cur_p for sig in LEGACY_PROMPT_SIGNATURES):
            self.data["system_prompt"] = get_prompt_for_language(self.data.get("output_language", "pt"))
            self.save()

        sync_storage_globals()

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
        sync_storage_globals()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()


config = ConfigManager()
sync_storage_globals()
