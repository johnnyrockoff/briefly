from unittest.mock import patch
import sys

from app.audio.devices import (
    get_default_sink,
    get_default_source,
    list_microphones,
    list_sinks,
    resolve_recording_devices,
)
from app.health import check_audio_server, check_ffmpeg


def test_windows_audio_defaults():
    with patch("sys.platform", "win32"):
        sink = get_default_sink()
        source = get_default_source()
        assert sink == "loopback"
        assert source == "default"

        sinks = list_sinks()
        assert len(sinks) >= 1
        assert sinks[0]["name"] == "loopback"
        assert sinks[0]["is_default"] is True

        mics = list_microphones()
        assert len(mics) >= 1
        assert mics[0]["name"] == "default"
        assert mics[0]["is_default"] is True

        mon, mic = resolve_recording_devices("auto", "auto")
        assert mon == "loopback"
        assert mic == "default"


def test_windows_health_check():
    with patch("sys.platform", "win32"):
        audio_health = check_audio_server()
        assert audio_health["status"] == "ok"
        assert "WASAPI" in audio_health["name"]

        with patch("shutil.which", return_value=None):
            ffmpeg_health = check_ffmpeg()
            assert ffmpeg_health["status"] == "error"
            assert "winget" in ffmpeg_health["action"]
