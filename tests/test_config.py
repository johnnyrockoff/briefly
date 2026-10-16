import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import ConfigManager, DEFAULT_CONFIG


def test_config_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        fake_legacy = Path(tmpdir) / "legacy.json"
        with patch("app.config.CONFIG_FILE", fake_cfg_file), patch("app.config.LEGACY_CONFIG_FILE", fake_legacy):
            cm = ConfigManager()
            assert cm.get("whisper_model") == "turbo"
            assert cm.get("ollama_model") == "qwen2.5:7b"
            assert cm.get("auto_transcribe") is True


def test_config_save_and_reload():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        fake_legacy = Path(tmpdir) / "legacy.json"
        with patch("app.config.CONFIG_FILE", fake_cfg_file), patch("app.config.LEGACY_CONFIG_FILE", fake_legacy):
            cm = ConfigManager()
            cm.set("whisper_model", "large-v3")
            cm.set("ollama_model", "llama3:8b")

            # Reload in new instance
            cm2 = ConfigManager()
            assert cm2.get("whisper_model") == "large-v3"
            assert cm2.get("ollama_model") == "llama3:8b"


def test_custom_storage_directory_and_subfolders():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        custom_storage = Path(tmpdir) / "MyCustomMeetingData"

        with patch("app.config.CONFIG_FILE", fake_cfg_file):
            from app.config import (
                config,
                get_recordings_dir,
                get_storage_base,
                get_summaries_dir,
                get_transcripts_dir,
                init_storage,
            )

            # Given: a custom storage directory path
            config.set("storage_dir", str(custom_storage))

            # When: querying storage base and subdirectories
            base = get_storage_base()
            rec = get_recordings_dir()
            txt = get_transcripts_dir()
            summ = get_summaries_dir()

            # Then: paths match the custom directory
            assert base == custom_storage.resolve()
            assert rec == custom_storage.resolve() / "recordings"
            assert txt == custom_storage.resolve() / "transcripts"
            assert summ == custom_storage.resolve() / "summaries"

            # And: subdirectories are created on disk
            init_storage()
            assert rec.is_dir()
            assert txt.is_dir()
            assert summ.is_dir()

            # Resetting to default (empty) reverts to default storage
            config.set("storage_dir", "")
            assert get_storage_base() != custom_storage.resolve()


def test_settings_dialog_storage_tab():
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from app.ui.components.settings_dialog import SettingsDialog
    except (ImportError, OSError):
        return

    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cfg_file = Path(tmpdir) / "config.json"
        custom_folder = Path(tmpdir) / "DialogCustomStorage"

        with patch("app.config.CONFIG_FILE", fake_cfg_file):
            from app.config import config
            dlg = SettingsDialog()

            # Given: user enters a custom folder in the storage input
            dlg.txt_storage_dir.setText(str(custom_folder))
            dlg._save_values()

            # Then: config receives the new custom storage path
            assert config.get("storage_dir") == str(custom_folder)

            # When: clicking reset to default
            dlg._reset_storage_dir()
            dlg._save_values()

            # Then: config reverts storage_dir to empty (default)
            assert config.get("storage_dir") == ""


