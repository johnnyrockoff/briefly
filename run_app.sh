#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Ambiente virtual não encontrado em $SCRIPT_DIR/.venv"
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
