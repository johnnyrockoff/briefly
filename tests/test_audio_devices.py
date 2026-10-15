from unittest.mock import patch

from app.audio.devices import resolve_recording_devices


def test_resolve_devices_with_auto():
    with patch("app.audio.devices.get_default_sink", return_value="alsa_output.headphones"), \
         patch("app.audio.devices.get_default_source", return_value="alsa_input.mic"):
        monitor, mic = resolve_recording_devices("auto", "auto")
        assert monitor == "alsa_output.headphones.monitor"
        assert mic == "alsa_input.mic"


def test_resolve_devices_with_custom():
    monitor, mic = resolve_recording_devices("custom_sink.monitor", "custom_mic")
    assert monitor == "custom_sink.monitor"
    assert mic == "custom_mic"


def test_resolve_devices_when_empty():
    with patch("app.audio.devices.get_default_sink", return_value=""), \
         patch("app.audio.devices.get_default_source", return_value=""):
        monitor, mic = resolve_recording_devices("auto", "auto")
        assert monitor is None
        assert mic is None
