#!/usr/bin/env bash
set -Eeuo pipefail

echo "=== Briefly Uninstaller ==="

if [[ "$(id -u)" -eq 0 ]]; then
    rm -rf /opt/briefly /opt/meeting-notes
    rm -f /usr/local/bin/briefly /usr/local/bin/meeting-notes /usr/bin/briefly /usr/bin/meeting-notes
    rm -f /usr/share/applications/briefly.desktop /usr/share/applications/meeting-notes.desktop
    rm -f /usr/share/icons/hicolor/scalable/apps/briefly.svg /usr/share/icons/hicolor/scalable/apps/meeting-notes.svg
else
    rm -rf "$HOME/.local/share/briefly" "$HOME/.local/share/meeting-notes"
    rm -f "$HOME/.local/bin/briefly" "$HOME/.local/bin/meeting-notes"
    rm -f "$HOME/.local/share/applications/briefly.desktop" "$HOME/.local/share/applications/meeting-notes.desktop"
    rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/briefly.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/meeting-notes.svg"
fi

echo "Briefly has been successfully removed from your system."
echo "(Your meeting files in ~/Documents/Briefly were preserved)."
