import os
import pytest

# Ensure offscreen Qt platform for headless CI runs
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from app.ui.components.record_card import RecordCard
    PYSIDE_AVAILABLE = True
except (ImportError, OSError):
    PYSIDE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PYSIDE_AVAILABLE,
    reason="PySide6 GUI libraries (libEGL/display) not available in headless environment"
)


@pytest.fixture(scope="session")
def qapp():
    if not PYSIDE_AVAILABLE:
        return None
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_timer_formatting_and_reset(qapp):
    card = RecordCard()

    # Initial state
    assert card.lbl_timer.text() == "00:00:00"

    # Simulate recording tick
    card.update_timer(3665)  # 1 hour, 1 minute, 5 seconds
    assert card.lbl_timer.text() == "01:01:05"

    # Stopping recording must reset timer to 00:00:00
    card.set_recording_state(False)
    assert card.lbl_timer.text() == "00:00:00"


def test_toggle_stop_resets_timer_immediately(qapp):
    card = RecordCard()
    card.set_recording_state(True)
    card.update_timer(42)
    assert card.lbl_timer.text() == "00:00:42"

    stop_called = []
    card.stop_requested.connect(lambda: stop_called.append(True))

    card._toggle_recording()
    assert card.lbl_timer.text() == "00:00:00"
    assert len(stop_called) == 1
