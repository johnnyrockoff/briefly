#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Briefly Installer ==="

# Check if Python 3.10+ is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Please install Python 3.10 or higher."
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "WARNING: ffmpeg not found in PATH. It is required to record meeting audio."
    echo "On Ubuntu/Debian: sudo apt install ffmpeg"
    echo "On Fedora: sudo dnf install ffmpeg"
    echo "On Arch Linux: sudo pacman -S ffmpeg"
fi

# If executed as root, install system-wide in /opt and /usr/local
if [[ "$(id -u)" -eq 0 ]]; then
    INSTALL_DIR="/opt/briefly"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor/scalable/apps"
else
    # User-level installation (no sudo required)
    INSTALL_DIR="$HOME/.local/share/briefly"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

echo "==> Copying files to $INSTALL_DIR..."
cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/main.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

# Create virtual environment
VENV_DIR="$INSTALL_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "==> Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    echo "==> Installing dependencies..."
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
fi

# Copy icon
cp "$INSTALL_DIR/app/resources/icon.svg" "$ICON_DIR/briefly.svg"

# Create binary launcher in PATH
LAUNCHER="$BIN_DIR/briefly"
cat << EOF > "$LAUNCHER"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python3" "$INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"

# Legacy alias
ln -sf "$LAUNCHER" "$BIN_DIR/meeting-notes"

# Create application menu entry (.desktop)
DESKTOP_FILE="$DESKTOP_DIR/briefly.desktop"
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Briefly
GenericName=AI Meeting Summaries
Comment=Record meetings, transcribe with Whisper and generate executive summaries with Ollama locally.
Exec=$LAUNCHER
Icon=$ICON_DIR/briefly.svg
Terminal=false
Categories=Utility;AudioVideo;Audio;Office;
Keywords=Briefly;Meeting;Notes;Whisper;Ollama;AI;Record;Summary;Transcription;
StartupNotify=true
StartupWMClass=briefly
EOF
chmod +x "$DESKTOP_FILE"

# Update desktop databases if tools exist
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo
echo "🎉 Briefly installed successfully!"
echo "• Launch it via terminal: briefly"
echo "• Or search for 'Briefly' in your application menu."
