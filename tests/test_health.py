from unittest.mock import patch

from app.health import check_ffmpeg, check_ollama_service, check_whisper_engine, run_full_system_check


def test_check_ffmpeg_missing():
    with patch("shutil.which", return_value=None):
        res = check_ffmpeg()
        assert res["status"] == "error"
        assert res["installed"] is False
        assert ("sudo" in res["action"] or "winget" in res["action"])


def test_check_ffmpeg_present():
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        res = check_ffmpeg()
        assert res["status"] == "ok"
        assert res["installed"] is True


def test_check_ollama_not_running():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        res = check_ollama_service()
        assert res["status"] == "warning"
        assert res["installed"] is False
        assert "ollama" in res["action"]


def test_full_system_check_structure():
    result = run_full_system_check()
    assert "overall" in result
    assert result["overall"] in ["ok", "warning", "error"]
    assert len(result["items"]) == 4
