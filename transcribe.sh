#!/usr/bin/env bash
set -Eeuo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECORDINGS_DIR="$BASE_DIR/recordings"
TRANSCRIPTS_DIR="$BASE_DIR/transcripts"
SUMMARIES_DIR="$BASE_DIR/summaries"
SUMMARY_SCRIPT="$BASE_DIR/summarize.py"

MODEL="small"
DEVICE="cuda"
FORCE=0
FILES=()

mkdir -p "$TRANSCRIPTS_DIR" "$SUMMARIES_DIR"

for arg in "$@"; do
    if [[ "$arg" == "--force" ]]; then
        FORCE=1
    else
        FILES+=("$arg")
    fi
done

# Preferir o Whisper instalado no ambiente virtual do projeto.
if [[ -x "$BASE_DIR/.venv/bin/whisper" ]]; then
    WHISPER="$BASE_DIR/.venv/bin/whisper"
elif command -v whisper >/dev/null 2>&1; then
    WHISPER="$(command -v whisper)"
else
    echo "ERRO: comando whisper não encontrado."
    echo "Ative seu ambiente virtual ou instale o Whisper nele."
    exit 1
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    shopt -s nullglob
    FILES=("$RECORDINGS_DIR"/reuniao_*.wav)
    shopt -u nullglob
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "Nenhuma gravação WAV encontrada em $RECORDINGS_DIR"
    exit 0
fi

for item in "${FILES[@]}"; do
    if [[ "$item" == *.wav ]]; then
        WAV="$item"
        [[ "$WAV" == /* ]] || WAV="$RECORDINGS_DIR/$WAV"
    else
        WAV="$RECORDINGS_DIR/$item.wav"
    fi

    if [[ ! -f "$WAV" ]]; then
        echo "ERRO: arquivo não encontrado: $WAV"
        continue
    fi

    STEM="$(basename "$WAV" .wav)"
    TXT="$TRANSCRIPTS_DIR/$STEM.txt"

    if [[ -s "$TXT" && "$FORCE" -eq 0 ]]; then
        echo "Transcrição já existe; ignorando: $TXT"
        continue
    fi

    echo
    echo "Transcrevendo: $WAV"
    echo "Modelo: $MODEL | Dispositivo: $DEVICE"

    if ! "$WHISPER" "$WAV" \
        --model "$MODEL" \
        --device "$DEVICE" \
        --output_dir "$TRANSCRIPTS_DIR" \
        --output_format all; then
        echo "ERRO na transcrição de $WAV"
        continue
    fi

    if [[ ! -s "$TXT" ]]; then
        echo "ERRO: Whisper não gerou o TXT esperado: $TXT"
        continue
    fi

    echo "Transcrição salva: $TXT"

    if [[ -f "$SUMMARY_SCRIPT" ]]; then
        echo "Gerando resumo com Ollama..."
        if [[ "$FORCE" -eq 1 ]]; then
            python3 "$SUMMARY_SCRIPT" --force "$STEM.txt"
        else
            python3 "$SUMMARY_SCRIPT" "$STEM.txt"
        fi
    else
        echo "Aviso: summarize.py não encontrado; resumo ignorado."
    fi
done

echo
echo "Processamento concluído."
