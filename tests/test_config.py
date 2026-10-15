import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import ConfigManager, DEFAULT_CONFIG


def test_config_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        with patch("app.config.CONFIG_FILE", fake_cfg_file):
            cm = ConfigManager()
            assert cm.get("whisper_model") == "small"
            assert cm.get("ollama_model") == "qwen2.5:7b"
            assert cm.get("auto_transcribe") is True


def test_config_save_and_reload():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        with patch("app.config.CONFIG_FILE", fake_cfg_file):
            cm = ConfigManager()
            cm.set("whisper_model", "large-v3")
            cm.set("ollama_model", "llama3:8b")

            # Reload in new instance
            cm2 = ConfigManager()
            assert cm2.get("whisper_model") == "large-v3"
            assert cm2.get("ollama_model") == "llama3:8b"
