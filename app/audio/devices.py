import json
import subprocess
import sys
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


def _list_windows_wasapi_devices() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    sinks = [{
        "name": "loopback",
        "monitor_name": "loopback",
        "description": "Default System Audio (WASAPI Loopback)",
        "is_default": True,
    }]
    mics = [{
        "name": "default",
        "description": "Default Microphone (WASAPI)",
        "is_default": True,
    }]

    try:
        res = subprocess.run(
            ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "wasapi", "-i", "dummy"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        lines = (res.stderr or "").splitlines()
        for line in lines:
            if '"' in line:
                dev_name = line.split('"')[1]
                if dev_name:
                    lower = line.lower()
                    if any(k in lower for k in ["render", "playback", "speaker", "headphone", "output"]):
                        sinks.append({
                            "name": f"loopback:{dev_name}",
                            "monitor_name": f"loopback:{dev_name}",
                            "description": dev_name,
                            "is_default": False,
                        })
                    elif any(k in lower for k in ["capture", "mic", "input"]):
                        mics.append({
                            "name": dev_name,
                            "description": dev_name,
                            "is_default": False,
                        })
    except Exception:
        pass

    return sinks, mics


def get_default_sink() -> str:
    if sys.platform == "win32":
        return "loopback"
    return _run_pactl_text(["get-default-sink"])


def get_default_source() -> str:
    if sys.platform == "win32":
        return "default"
    return _run_pactl_text(["get-default-source"])


def list_sinks() -> List[Dict[str, str]]:
    """
    Returns list of sinks (audio output devices) with keys:
    - 'name': technical sink name
    - 'monitor_name': monitor source name
    - 'description': human readable name
    - 'is_default': bool
    """
    if sys.platform == "win32":
        sinks, _ = _list_windows_wasapi_devices()
        return sinks

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
    Returns list of microphones with keys:
    - 'name': technical source name
    - 'description': human readable name
    - 'is_default': bool
    """
    if sys.platform == "win32":
        _, mics = _list_windows_wasapi_devices()
        return mics

    default_source = get_default_source()
    raw = _run_pactl_json(["list", "sources"])
    mics = []
    for item in raw:
        name = item.get("name", "")
        if not name:
            continue
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
    Resolves actual device names for FFmpeg (WASAPI on Windows, PulseAudio/PipeWire on Linux).
    Returns (monitor_source_name, mic_source_name).
    """
    if sys.platform == "win32":
        monitor = "loopback" if (selected_sink_monitor == "auto" or not selected_sink_monitor) else selected_sink_monitor
        mic = "default" if (selected_mic == "auto" or not selected_mic) else selected_mic
        return monitor, mic

    # Linux (PulseAudio / PipeWire)
    if selected_sink_monitor == "auto" or not selected_sink_monitor:
        def_sink = get_default_sink()
        if def_sink:
            resolved_monitor = f"{def_sink}.monitor"
        else:
            resolved_monitor = None
    else:
        resolved_monitor = selected_sink_monitor

    if selected_mic == "auto" or not selected_mic:
        def_source = get_default_source()
        resolved_mic = def_source if def_source else None
    else:
        resolved_mic = selected_mic

    return resolved_monitor, resolved_mic
