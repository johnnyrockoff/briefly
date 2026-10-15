#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="${1:-1.0.0}"
PKG_NAME="briefly"
TARGET_DIR="$ROOT_DIR/dist/${PKG_NAME}-${VERSION}-linux-portable"
TARBALL="$ROOT_DIR/dist/${PKG_NAME}-${VERSION}-linux-portable.tar.gz"

echo "==> Building Briefly portable bundle..."
rm -rf "$TARGET_DIR" "$TARBALL"
mkdir -p "$TARGET_DIR"

cp -r "$ROOT_DIR/app" "$TARGET_DIR/"
cp "$ROOT_DIR/main.py" "$TARGET_DIR/"
cp "$ROOT_DIR/requirements.txt" "$TARGET_DIR/"
cp "$ROOT_DIR/install.sh" "$TARGET_DIR/"
cp "$ROOT_DIR/uninstall.sh" "$TARGET_DIR/"
cp "$ROOT_DIR/README.md" "$TARGET_DIR/"
cp "$ROOT_DIR/pyproject.toml" "$TARGET_DIR/"
cp "$ROOT_DIR/briefly.desktop" "$TARGET_DIR/"

cat << 'EOF' > "$TARGET_DIR/run.sh"
#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$DIR/.venv" ]]; then
    echo "Configuring portable environment..."
    python3 -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install --upgrade pip
    "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
fi
exec "$DIR/.venv/bin/python3" "$DIR/main.py" "$@"
EOF
chmod +x "$TARGET_DIR/run.sh"

echo "==> Packaging into $TARBALL..."
tar -czf "$TARBALL" -C "$ROOT_DIR/dist" "${PKG_NAME}-${VERSION}-linux-portable"
rm -rf "$TARGET_DIR"

echo "==> Portable bundle ready:"
ls -lh "$TARBALL"
