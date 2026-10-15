import os
import sys
from unittest.mock import patch

from app.config import LOCAL_BIN_DIR
from app.hardware import detect_system_hardware
from app.installer import DependencyInstaller, InstallWorker


def test_hardware_detection_cpu_fallback():
    with patch("torch.cuda.is_available", return_value=False):
        hw = detect_system_hardware()
        assert "profile_key" in hw
        assert "recommended_whisper" in hw
        assert "recommended_ollama" in hw
        assert hw["has_gpu"] is False


def test_hardware_detection_gpu_profile():
    mock_torch = patch("torch.cuda.is_available", return_value=True)
    mock_device = patch("torch.cuda.get_device_name", return_value="NVIDIA GeForce RTX 4070")

    with mock_torch, mock_device:
        hw = detect_system_hardware()
        assert hw["has_gpu"] is True
        assert hw["recommended_whisper"] == "small"
        assert hw["recommended_ollama"] == "qwen2.5:7b"


def test_local_bin_in_path():
    assert str(LOCAL_BIN_DIR) in os.environ["PATH"]


def test_installer_lifecycle():
    installer = DependencyInstaller()
    assert installer.is_busy is False

    worker = InstallWorker("unknown_task")
    assert worker.task_type == "unknown_task"
    worker.cancel()
    assert worker._is_cancelled is True
