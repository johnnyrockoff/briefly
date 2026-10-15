import io
import json
from unittest.mock import MagicMock, patch

from app.summarization.summarizer import SummarizerWorker


def test_summarizer_worker_mock(tmp_path):
    fake_txt = tmp_path / "reuniao_teste.txt"
    fake_txt.write_text("Discutimos a entrega da funcionalidade de relatórios para o dia 20.", encoding="utf-8")

    worker = SummarizerWorker(str(fake_txt))

    # Mock chunk do ollama stream
    fake_response_data = [
        json.dumps({"message": {"content": "# Meeting Summary\nDeliveries aligned."}}).encode("utf-8") + b"\n"
    ]

    mock_resp = io.BytesIO(b"".join(fake_response_data))
    mock_resp.__enter__ = MagicMock(return_value=fake_response_data)
    mock_resp.__exit__ = MagicMock(return_value=False)

    finished_called = []
    def on_finished(txt_path, md_path, summary):
        finished_called.append((txt_path, md_path, summary))

    worker.finished.connect(on_finished)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        worker.run()

    assert len(finished_called) == 1
    assert "Meeting Summary" in finished_called[0][2]
