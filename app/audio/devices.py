import json
import subprocess
from typing import Dict, List, Optional, Tuple


def _run_pactl_json(args: List[str]) -> List[dict]:
    try:
        res = subprocess.run(
            ["pactl", "-f", "json", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        if isinstance(data, list):
            return data
        return [data]
    except Exception:
        return []


def _run_pactl_text(args: List[str]) -> str:
    try:
        res = subprocess.run(
            ["pactl", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return ""


def get_default_sink() -> str:
    return _run_pactl_text(["get-default-sink"])


def get_default_source() -> str:
    return _run_pactl_text(["get-default-source"])


def list_sinks() -> List[Dict[str, str]]:
    """
    Returns list of sinks (audio output devices) with keys:
    - 'name': technical sink name
    - 'monitor_name': monitor source name (<name>.monitor)
    - 'description': human readable name
    - 'is_default': bool
    """
    default_sink = get_default_sink()
    raw = _run_pactl_json(["list", "sinks"])
    sinks = []
    for item in raw:
        name = item.get("name", "")
        if not name:
            continue
        desc = item.get("description", "") or item.get("properties", {}).get("device.description", name)
        monitor_name = item.get("monitor_source", f"{name}.monitor") or f"{name}.monitor"
        sinks.append({
            "name": name,
            "monitor_name": monitor_name,
            "description": desc,
            "is_default": (name == default_sink),
        })
    return sinks


def list_microphones() -> List[Dict[str, str]]:
    """
    Returns list of microphones (excluding monitors) with keys:
    - 'name': technical source name
    - 'description': human readable name
    - 'is_default': bool
    """
    default_source = get_default_source()
    raw = _run_pactl_json(["list", "sources"])
    mics = []
    for item in raw:
        name = item.get("name", "")
        if not name:
            continue
        # Ignorar monitores de sinks para a lista de microfones
        if name.endswith(".monitor") or item.get("monitor_source"):
            continue
        desc = item.get("description", "") or item.get("properties", {}).get("device.description", name)
        mics.append({
            "name": name,
            "description": desc,
            "is_default": (name == default_source),
        })
    return mics


def resolve_recording_devices(
    selected_sink_monitor: str = "auto",
    selected_mic: str = "auto"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves actual PulseAudio/PipeWire device names for FFmpeg.
    Returns (monitor_source_name, mic_source_name).
    """
    # Resolve monitor (computador/reuniao)
    if selected_sink_monitor == "auto" or not selected_sink_monitor:
        def_sink = get_default_sink()
        if def_sink:
            resolved_monitor = f"{def_sink}.monitor"
        else:
            resolved_monitor = None
    else:
        resolved_monitor = selected_sink_monitor

    # Resolve mic
    if selected_mic == "auto" or not selected_mic:
        def_source = get_default_source()
        resolved_mic = def_source if def_source else None
    else:
        resolved_mic = selected_mic

    return resolved_monitor, resolved_mic
