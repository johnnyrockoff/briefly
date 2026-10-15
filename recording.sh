#!/usr/bin/env bash
set -Eeuo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECORDINGS_DIR="${RECORDINGS_DIR:-$BASE_DIR/recordings}"
STATE_FILE="$BASE_DIR/.recording-state"
LOG_FILE="$BASE_DIR/.recording.log"

# Detecção automática de dispositivos padrão se não informados por variável de ambiente
DEFAULT_SINK="$(pactl get-default-sink 2>/dev/null || echo "")"
MONITOR="${MONITOR:-${DEFAULT_SINK:+$DEFAULT_SINK.monitor}}"
MIC="${MIC:-$(pactl get-default-source 2>/dev/null || echo "")}"

mkdir -p "$RECORDINGS_DIR"

is_recording() {
    [[ -f "$STATE_FILE" ]] || return 1
    local pid
    pid="$(head -n 1 "$STATE_FILE")"
    [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

start_recording() {
    if is_recording; then
        echo "Já existe uma gravação em andamento."
        exit 1
    fi

    local timestamp output
    timestamp="$(date +'%Y-%m-%d_%H-%M-%S')"
    output="$RECORDINGS_DIR/reuniao_${timestamp}.wav"

    echo "Iniciando gravação..."
    echo "Arquivo: $output"

    nohup ffmpeg -hide_banner -nostdin -y \
        -thread_queue_size 1024 \
        -f pulse -i "$MONITOR" \
        -thread_queue_size 1024 \
        -f pulse -i "$MIC" \
        -filter_complex \
        "[0:a]aresample=16000,aformat=channel_layouts=mono[out];[1:a]aresample=16000,aformat=channel_layouts=mono[mic];[out][mic]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0,alimiter=limit=0.95[mix]" \
        -map "[mix]" -ac 1 -ar 16000 -c:a pcm_s16le \
        "$output" > "$LOG_FILE" 2>&1 &

    local pid=$!
    printf '%s\n%s\n' "$pid" "$output" > "$STATE_FILE"
    sleep 2

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "ERRO: o FFmpeg não permaneceu em execução."
        cat "$LOG_FILE"
        rm -f "$STATE_FILE"
        exit 1
    fi

    echo "Gravação iniciada. PID: $pid"
    echo "Para encerrar: ./recording.sh stop"
}

stop_recording() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "Nenhuma gravação registrada."
        exit 1
    fi

    local pid output
    pid="$(sed -n '1p' "$STATE_FILE")"
    output="$(sed -n '2p' "$STATE_FILE")"

    if [[ ! "$pid" =~ ^[0-9]+$ ]]; then
        echo "Estado da gravação inválido: $STATE_FILE"
        exit 1
    fi

    if kill -0 "$pid" 2>/dev/null; then
        echo "Finalizando gravação..."
        kill -INT "$pid"

        for _ in $(seq 1 60); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 1
        done

        if kill -0 "$pid" 2>/dev/null; then
            echo "O FFmpeg ainda está encerrando. Verifique: $LOG_FILE"
            exit 1
        fi
    fi

    rm -f "$STATE_FILE"

    if [[ -s "$output" ]]; then
        echo "Gravação finalizada: $output"
    else
        echo "ERRO: o arquivo não foi criado ou está vazio."
        cat "$LOG_FILE"
        exit 1
    fi
}

show_status() {
    if is_recording; then
        echo "Gravação em andamento."
        sed -n '2p' "$STATE_FILE"
    else
        echo "Nenhuma gravação em andamento."
        if [[ -f "$STATE_FILE" ]]; then
            echo "Existe um estado antigo; verifique antes de removê-lo:"
            cat "$STATE_FILE"
        fi
    fi
}

case "${1:-}" in
    start)  start_recording ;;
    stop)   stop_recording ;;
    status) show_status ;;
    *)
        echo "Uso: $0 {start|stop|status}"
        exit 2
        ;;
esac
