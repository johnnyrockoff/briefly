import io
import os
import tarfile
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from app.config import MODELS_DIR

SEGMENTATION_MODEL_NAME = "sherpa-onnx-pyannote-segmentation-3-0.onnx"
EMBEDDING_MODEL_NAME = "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"

SEGMENTATION_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/"
    "sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
)
EMBEDDING_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"
    "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"
)


def get_diarizer_model_paths() -> Tuple[Path, Path]:
    """Returns local paths for segmentation and embedding ONNX models."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return (
        MODELS_DIR / SEGMENTATION_MODEL_NAME,
        MODELS_DIR / EMBEDDING_MODEL_NAME,
    )


def are_diarizer_models_available() -> bool:
    """Checks whether both required ONNX models are present on disk."""
    seg, emb = get_diarizer_model_paths()
    return seg.is_file() and emb.is_file() and seg.stat().st_size > 1000 and emb.stat().st_size > 1000


def ensure_diarizer_models(progress_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Downloads segmentation (~6 MB) and 3D-Speaker embedding (~38 MB) models
    automatically from official releases if not already present.
    """
    seg_path, emb_path = get_diarizer_model_paths()
    if are_diarizer_models_available():
        return True

    try:
        if not seg_path.exists():
            if progress_callback:
                progress_callback("Baixando modelo de segmentação de locutores (~6 MB)...")
            req = urllib.request.Request(SEGMENTATION_URL, headers={"User-Agent": "Briefly/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()

            with tarfile.open(fileobj=io.BytesIO(data), mode="r:bz2") as tar:
                for member in tar.getmembers():
                    if member.name.endswith("model.onnx"):
                        extracted = tar.extractfile(member)
                        if extracted:
                            seg_path.write_bytes(extracted.read())
                        break

        if not emb_path.exists():
            if progress_callback:
                progress_callback("Baixando modelo acústico 3D-Speaker (~38 MB)...")
            req = urllib.request.Request(EMBEDDING_URL, headers={"User-Agent": "Briefly/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                emb_path.write_bytes(resp.read())

        return are_diarizer_models_available()
    except Exception as e:
        if progress_callback:
            progress_callback(f"Aviso: Não foi possível baixar modelos de diarização: {e}")
        return False


def diarize_audio(
    wav_path: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[Tuple[float, float, int]]:
    """
    Executes neural speaker diarization on 16kHz mono audio.
    Returns a list of (start_time, end_time, speaker_id).
    """
    try:
        import sherpa_onnx
        import whisper
    except ImportError as e:
        if progress_callback:
            progress_callback(f"Aviso: sherpa-onnx não disponível para diarização ({e})")
        return []

    if not ensure_diarizer_models(progress_callback):
        return []

    seg_path, emb_path = get_diarizer_model_paths()

    try:
        config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
            segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
                pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=str(seg_path)),
            ),
            embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(emb_path)),
            clustering=sherpa_onnx.FastClusteringConfig(threshold=0.5),
        )

        if not config.validate():
            return []

        sd = sherpa_onnx.OfflineSpeakerDiarization(config)
        samples = whisper.load_audio(wav_path)

        def _cb(processed: int, total: int):
            if progress_callback and total > 0:
                pct = int((processed / total) * 100)
                progress_callback(f"Identificando interlocutores ({pct}%)...")
            return 0

        res = sd.process(samples, callback=_cb)
        segments = res.sort_by_start_time()
        return [(float(s.start), float(s.end), int(s.speaker)) for s in segments]
    except Exception as e:
        if progress_callback:
            progress_callback(f"Falha na diarização de áudio: {e}")
        return []


def merge_whisper_and_diarization(
    whisper_segments: List[Dict],
    diarization_segments: List[Tuple[float, float, int]],
) -> List[Dict]:
    """
    Aligns each transcribed Whisper phrase with the corresponding speaker ID
    based on maximum temporal overlap.
    """
    annotated = []
    last_speaker = 0

    for w in whisper_segments:
        text = w.get("text", "").strip()
        if not text:
            continue

        w_start = float(w.get("start", 0.0))
        w_end = float(w.get("end", 0.0))

        best_speaker = None
        max_overlap = 0.0

        for d_start, d_end, d_spk in diarization_segments:
            overlap = max(0.0, min(w_end, d_end) - max(w_start, d_start))
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = d_spk

        # If no strict overlap (e.g. short sentence between diarized regions)
        if best_speaker is None:
            min_dist = float("inf")
            for d_start, d_end, d_spk in diarization_segments:
                dist = min(abs(w_start - d_end), abs(w_end - d_start))
                if dist < min_dist and dist < 2.0:
                    min_dist = dist
                    best_speaker = d_spk

            if best_speaker is None:
                best_speaker = last_speaker

        last_speaker = best_speaker
        annotated.append({
            "start": w_start,
            "end": w_end,
            "speaker": best_speaker,
            "text": text,
        })

    return annotated


def format_timestamp(seconds: float) -> str:
    """Formats seconds into mm:ss or hh:mm:ss."""
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_annotated_transcript(
    annotated_segments: List[Dict],
    include_timestamps: bool = True,
) -> str:
    """
    Formats segments into speaker dialogue:
    [00:00:05] Interlocutor 1: bla bla bla
    [00:00:15] Interlocutor 2: bla bla bla
    """
    if not annotated_segments:
        return ""

    # Map raw cluster speaker IDs to chronological order (Interlocutor 1, 2, ...)
    speaker_map = {}
    for seg in annotated_segments:
        raw_spk = seg["speaker"]
        if raw_spk not in speaker_map:
            speaker_map[raw_spk] = len(speaker_map) + 1
        seg["speaker_num"] = speaker_map[raw_spk]

    lines = []
    current_spk = None
    current_texts = []
    current_start = 0.0

    for seg in annotated_segments:
        spk = seg["speaker_num"]
        if spk != current_spk:
            if current_texts:
                prefix = f"[{format_timestamp(current_start)}] " if include_timestamps else ""
                lines.append(f"{prefix}Interlocutor {current_spk}: {' '.join(current_texts)}")
            current_spk = spk
            current_texts = [seg["text"]]
            current_start = seg["start"]
        else:
            current_texts.append(seg["text"])

    if current_texts:
        prefix = f"[{format_timestamp(current_start)}] " if include_timestamps else ""
        lines.append(f"{prefix}Interlocutor {current_spk}: {' '.join(current_texts)}")

    return "\n\n".join(lines)
