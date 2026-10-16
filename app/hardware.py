import os
import shutil
import sys
from typing import Any, Dict


def detect_system_hardware() -> Dict[str, Any]:
    """
    Detects hardware capabilities (GPU acceleration, memory) and recommends
    optimized model configurations for Whisper and Ollama.
    """
    has_cuda = False
    has_rocm = False
    gpu_name = None

    try:
        import torch
        if torch.cuda.is_available():
            has_cuda = True
            gpu_name = torch.cuda.get_device_name(0)
            if "AMD" in gpu_name or "Radeon" in gpu_name:
                has_rocm = True
    except Exception:
        pass

    # RAM estimation
    total_ram_gb = 8.0
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_ram_gb = stat.ullTotalPhys / (1024 ** 3)
        else:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        kb = int(line.split()[1])
                        total_ram_gb = kb / (1024 ** 2)
                        break
    except Exception:
        pass

    # Determine recommended profile
    if has_cuda or has_rocm:
        profile_key = "gpu_balanced"
        profile_title = "GPU Accelerated"
        rec_whisper = "turbo"
        rec_ollama = "qwen2.5:7b"
        device_type = f"GPU ({gpu_name})"
        note = "Hardware acceleration active for fast transcription and AI summaries."
    elif total_ram_gb >= 15.0:
        profile_key = "cpu_standard"
        profile_title = "High-Memory CPU"
        rec_whisper = "base"
        rec_ollama = "qwen2.5:7b"
        device_type = f"CPU ({total_ram_gb:.0f} GB RAM)"
        note = "Sufficient RAM for standard 7B models on CPU."
    else:
        profile_key = "cpu_light"
        profile_title = "Lightweight / Laptop (CPU)"
        rec_whisper = "base"
        rec_ollama = "qwen2.5:3b"
        device_type = f"CPU ({total_ram_gb:.0f} GB RAM)"
        note = "Optimized for speed and minimal RAM consumption (3B parameter model)."

    return {
        "has_gpu": has_cuda or has_rocm,
        "gpu_name": gpu_name,
        "ram_gb": round(total_ram_gb, 1),
        "device_type": device_type,
        "profile_key": profile_key,
        "profile_title": profile_title,
        "recommended_whisper": rec_whisper,
        "recommended_ollama": rec_ollama,
        "note": note,
    }
