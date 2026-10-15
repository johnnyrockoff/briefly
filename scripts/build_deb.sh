#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="${1:-1.0.0}"
# Sanitize version string for Debian package format (replaces / with - and removes invalid chars)
VERSION="$(echo "$VERSION" | tr '/' '-' | tr -cd 'a-zA-Z0-9.+~-')"
PKG_NAME="briefly"
ARCH="all"
BUILD_ROOT="$ROOT_DIR/dist/deb-build"
PKG_DIR="$BUILD_ROOT/${PKG_NAME}_${VERSION}_${ARCH}"

echo "==> Cleaning previous build directories..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$PKG_DIR/opt/$PKG_NAME"

echo "==> Copying application files to /opt/$PKG_NAME..."
cp -r "$ROOT_DIR/app" "$PKG_DIR/opt/$PKG_NAME/"
cp "$ROOT_DIR/main.py" "$PKG_DIR/opt/$PKG_NAME/"
cp "$ROOT_DIR/requirements.txt" "$PKG_DIR/opt/$PKG_NAME/"
cp "$ROOT_DIR/run_app.sh" "$PKG_DIR/opt/$PKG_NAME/"

# System icon
cp "$ROOT_DIR/app/resources/icon.svg" "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/briefly.svg"

# Desktop menu entry
cat << 'EOF' > "$PKG_DIR/usr/share/applications/briefly.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Briefly
GenericName=AI Meeting Summaries
Comment=Record meetings, transcribe with Whisper and generate executive summaries with Ollama locally.
Exec=/usr/bin/briefly
Icon=briefly
Terminal=false
Categories=Utility;AudioVideo;Audio;Office;
Keywords=Briefly;Meeting;Notes;Whisper;Ollama;AI;Record;Summary;Transcription;
StartupNotify=true
StartupWMClass=briefly
EOF

# Binary launcher in /usr/bin/briefly
cat << 'EOF' > "$PKG_DIR/usr/bin/briefly"
#!/usr/bin/env bash
set -e

APP_DIR="/opt/briefly"
VENV_DIR="$APP_DIR/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Initializing Briefly environment for the first time..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
fi

exec "$VENV_DIR/bin/python3" "$APP_DIR/main.py" "$@"
EOF
chmod +x "$PKG_DIR/usr/bin/briefly"

# Symlink legacy command for convenience
ln -sf /usr/bin/briefly "$PKG_DIR/usr/bin/meeting-notes"

# Debian control file
cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: ffmpeg, python3 (>= 3.10), python3-venv, python3-pip
Recommends: pulseaudio-utils | pipewire-bin
Maintainer: Johnny Rocha <johnny@local>
Description: Briefly - Intelligent Local AI Meeting Summarizer
 Native Linux desktop application that records system audio and microphone,
 transcribes locally with OpenAI Whisper, and summarizes using Ollama LLMs.
EOF

# Postinst script
cat << 'EOF' > "$PKG_DIR/DEBIAN/postinst"
#!/usr/bin/env bash
set -e
chmod -R a+rX /opt/briefly
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod +x "$PKG_DIR/DEBIAN/postinst"

echo "==> Building .deb package..."
mkdir -p "$ROOT_DIR/dist"
dpkg-deb --build --root-owner-group "$PKG_DIR" "$ROOT_DIR/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "==> .deb package built successfully:"
ls -lh "$ROOT_DIR/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
