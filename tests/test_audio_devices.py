from unittest.mock import patch

from app.audio.devices import resolve_recording_devices


def test_resolve_devices_with_auto():
    with patch("sys.platform", "linux"), \
         patch("app.audio.devices.get_default_sink", return_value="alsa_output.headphones"), \
         patch("app.audio.devices.get_default_source", return_value="alsa_input.mic"):
        monitor, mic = resolve_recording_devices("auto", "auto")
        assert monitor == "alsa_output.headphones.monitor"
        assert mic == "alsa_input.mic"


def test_resolve_devices_with_custom():
    monitor, mic = resolve_recording_devices("custom_sink.monitor", "custom_mic")
    assert monitor == "custom_sink.monitor"
    assert mic == "custom_mic"


def test_resolve_devices_when_empty():
    with patch("sys.platform", "linux"), \
         patch("app.audio.devices.get_default_sink", return_value=""), \
         patch("app.audio.devices.get_default_source", return_value=""):
        monitor, mic = resolve_recording_devices("auto", "auto")
        assert monitor is None
        assert mic is None


def test_audio_recorder_cmd_includes_dynaudnorm(tmp_path):
    from unittest.mock import MagicMock
    from app.audio.recorder import AudioRecorder

    with patch("app.audio.recorder.resolve_recording_devices", return_value=("sink.monitor", "mic.source")), \
         patch("app.audio.recorder.get_recordings_dir", return_value=tmp_path), \
         patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        rec = AudioRecorder()
        assert rec.start_recording() is True

        called_cmd = mock_popen.call_args[0][0]
        # Verify dynaudnorm and alimiter are in the filter chain
        filter_str = " ".join(called_cmd)
        assert "dynaudnorm=f=150:g=15:m=20.0:r=0.9:b=1" in filter_str
        assert "alimiter=limit=0.95" in filter_str
        assert "amix=inputs=2" in filter_str

        # Cleanup recorder log handle
        if hasattr(rec, "_log_handle") and rec._log_handle:
            rec._log_handle.close()


def test_transcription_worker_optimized_kwargs(tmp_path):
    from unittest.mock import MagicMock
    from app.transcription.transcriber import TranscriptionWorker

    fake_wav = tmp_path / "audio.wav"
    fake_wav.write_bytes(b"RIFFdummydata")

    with patch("whisper.load_model") as mock_load, \
         patch("torch.cuda.is_available", return_value=True), \
         patch("app.transcription.transcriber.get_transcripts_dir", return_value=tmp_path), \
         patch.dict("app.config.config.data", {"input_language": "pt", "whisper_model": "turbo", "whisper_device": "cuda"}):

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Transcrição de teste"}
        mock_load.return_value = mock_model

        worker = TranscriptionWorker(str(fake_wav))
        worker.run()

        mock_model.transcribe.assert_called_once()
        _, kwargs = mock_model.transcribe.call_args

        assert kwargs["beam_size"] == 5
        assert kwargs["best_of"] == 5
        assert kwargs["temperature"] == (0.0, 0.2)
        assert kwargs["condition_on_previous_text"] is False
        assert kwargs["compression_ratio_threshold"] == 2.4
        assert kwargs["no_speech_threshold"] == 0.6
        assert kwargs["language"] == "pt"
        assert kwargs["fp16"] is True
        assert "Reunião corporativa" in kwargs["initial_prompt"]
