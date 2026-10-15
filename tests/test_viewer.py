import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from app.ui.components.viewer import MeetingViewer
    from app.ui.components.meetings_list import MeetingsList
    PYSIDE_AVAILABLE = True
except (ImportError, OSError):
    PYSIDE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PYSIDE_AVAILABLE,
    reason="PySide6 GUI libraries not available in headless environment"
)


@pytest.fixture(scope="session")
def qapp():
    if not PYSIDE_AVAILABLE:
        return None
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_viewer_clear_state(qapp):
    # Given: a viewer instance
    viewer = MeetingViewer()

    # When: calling clear()
    viewer.clear()

    # Then: state is completely reset and buttons are disabled
    assert viewer.current_stem is None
    assert viewer.lbl_title.text() == "Select a Meeting"
    assert viewer.btn_transcribe.isEnabled() is False
    assert viewer.btn_summarize.isEnabled() is False
    assert viewer.btn_copy_markdown.isEnabled() is False
    assert viewer.btn_open_external.isEnabled() is False
    assert viewer.edit_raw_markdown.toPlainText() == ""
    assert "No Meeting Selected" in viewer.browser_summary.toHtml()


def test_viewer_load_empty_stem_triggers_clear(qapp):
    viewer = MeetingViewer()
    viewer.current_stem = "reuniao_2026-10-15_12-00-00"
    viewer.lbl_title.setText("Old Meeting")

    # When loading empty stem
    viewer.load_meeting("")

    # Then it automatically clears
    assert viewer.current_stem is None
    assert viewer.lbl_title.text() == "Select a Meeting"


def test_meetings_list_empty_emits_empty_selection(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / "empty_storage"
        empty_dir.mkdir(parents=True, exist_ok=True)

        with patch("app.ui.components.meetings_list.get_recordings_dir", return_value=empty_dir / "recordings"), \
             patch("app.ui.components.meetings_list.get_transcripts_dir", return_value=empty_dir / "transcripts"), \
             patch("app.ui.components.meetings_list.get_summaries_dir", return_value=empty_dir / "summaries"):

            meetings_list = MeetingsList()
            received_stems = []
            meetings_list.meeting_selected.connect(lambda s: received_stems.append(s))

            # When: reloading meetings on empty storage
            meetings_list.reload_meetings()

            # Then: meetings_selected was emitted with empty string
            assert received_stems == [""]
            assert meetings_list.list_widget.count() == 0
