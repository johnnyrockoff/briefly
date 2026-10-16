from pathlib import Path
from unittest.mock import MagicMock, patch

from app.transcription.diarizer import (
    format_annotated_transcript,
    format_timestamp,
    get_diarizer_model_paths,
    merge_whisper_and_diarization,
)
from app.transcription.transcriber import TranscriptionWorker


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(45) == "00:45"
    assert format_timestamp(75) == "01:15"
    assert format_timestamp(3665) == "01:01:05"


def test_merge_whisper_and_diarization_basic():
    # Given Whisper phrases and diarized intervals
    whisper_segments = [
        {"start": 1.0, "end": 4.0, "text": "Bom dia a todos."},
        {"start": 4.5, "end": 8.0, "text": "Olá! Vamos começar."},
        {"start": 8.5, "end": 12.0, "text": "Perfeito, qual é a pauta?"},
    ]

    diarization_segments = [
        (0.8, 4.2, 0),    # Speaker 0: 1.0 - 4.0
        (4.4, 8.2, 1),    # Speaker 1: 4.5 - 8.0
        (8.3, 12.5, 0),   # Speaker 0: 8.5 - 12.0
    ]

    # When merging
    merged = merge_whisper_and_diarization(whisper_segments, diarization_segments)

    # Then each segment is attributed to the correct speaker
    assert len(merged) == 3
    assert merged[0]["speaker"] == 0
    assert merged[0]["text"] == "Bom dia a todos."
    assert merged[1]["speaker"] == 1
    assert merged[1]["text"] == "Olá! Vamos começar."
    assert merged[2]["speaker"] == 0
    assert merged[2]["text"] == "Perfeito, qual é a pauta?"


def test_format_annotated_transcript_grouping_and_labels():
    annotated = [
        {"start": 1.0, "end": 3.0, "speaker": 10, "text": "Primeira frase."},
        {"start": 3.5, "end": 5.0, "speaker": 10, "text": "Segunda frase do mesmo interlocutor."},
        {"start": 5.5, "end": 7.0, "speaker": 20, "text": "Resposta de outro participante."},
        {"start": 7.5, "end": 9.0, "speaker": 10, "text": "Retorno do primeiro interlocutor."},
    ]

    formatted = format_annotated_transcript(annotated, include_timestamps=True)

    # Must label chronologically: speaker 10 -> Interlocutor 1, speaker 20 -> Interlocutor 2
    assert "Interlocutor 1: Primeira frase. Segunda frase do mesmo interlocutor." in formatted
    assert "Interlocutor 2: Resposta de outro participante." in formatted
    assert "Interlocutor 1: Retorno do primeiro interlocutor." in formatted
    assert "[00:01] Interlocutor 1:" in formatted
    assert "[00:05] Interlocutor 2:" in formatted


def test_transcription_worker_produces_diarized_output(tmp_path):
    fake_wav = tmp_path / "meeting.wav"
    fake_wav.write_bytes(b"RIFFdummydata")

    fake_result = {
        "text": "Bom dia. Olá, como vai? Tudo bem.",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Bom dia."},
            {"start": 2.5, "end": 4.5, "text": "Olá, como vai?"},
            {"start": 5.0, "end": 7.0, "text": "Tudo bem."},
        ],
    }

    fake_diar_segments = [
        (0.0, 2.2, 0),
        (2.4, 4.6, 1),
        (4.9, 7.1, 0),
    ]

    with patch("whisper.load_model") as mock_load, \
         patch("torch.cuda.is_available", return_value=True), \
         patch("app.transcription.transcriber.get_transcripts_dir", return_value=tmp_path), \
         patch("app.transcription.diarizer.diarize_audio", return_value=fake_diar_segments) as mock_diar, \
         patch.dict("app.config.config.data", {"enable_diarization": True, "input_language": "pt", "whisper_model": "turbo"}):

        mock_model = MagicMock()
        mock_model.transcribe.return_value = fake_result
        mock_load.return_value = mock_model

        worker = TranscriptionWorker(str(fake_wav))
        worker.run()

        mock_diar.assert_called_once()

        saved_txt = tmp_path / "meeting.txt"
        assert saved_txt.exists()
        content = saved_txt.read_text(encoding="utf-8")

        # Verify formatting matches Interlocutor 1 and Interlocutor 2
        assert "Interlocutor 1: Bom dia." in content
        assert "Interlocutor 2: Olá, como vai?" in content
        assert "Interlocutor 1: Tudo bem." in content
