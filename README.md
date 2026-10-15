# 🎙️ Briefly

[![Linux](https://img.shields.io/badge/OS-Linux-FCC624?logo=linux&logoColor=black)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Qt6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?logo=qt&logoColor=white)](https://qt.io)
[![Whisper](https://img.shields.io/badge/AI-OpenAI%20Whisper-brightgreen)](https://github.com/openai/whisper)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20Local-orange)](https://ollama.ai)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Briefly** is an intelligent, privacy-first native Linux desktop app that records online meetings (capturing both other participants and your microphone), generates high-fidelity offline transcriptions with **OpenAI Whisper** (GPU-accelerated via NVIDIA CUDA), and crafts structured executive summaries using local LLMs via **Ollama** (`qwen2.5:7b`).

---

## ✨ Features

- 🎧 **Smart Audio Mixing**: Seamlessly records call audio (system monitor/headphones) and your microphone via PulseAudio / PipeWire, mixed into normalized 16 kHz mono with peak limiting.
- 🚀 **System Tray Daemon**: Start, pause, or stop recordings with a single click even when the window is hidden during Google Meet, Zoom, Teams, or Discord calls.
- 🩺 **Built-in System Diagnostics**: Automatic health check verifying FFmpeg, PipeWire/PulseAudio devices, PyTorch/CUDA readiness, and Ollama service connectivity with one-click fix suggestions.
- 🔒 **100% Offline & Private**: Audio processing, transcription, and summarization never leave your machine — no subscriptions, no cloud uploads.
- 📋 **Executive Markdown Summaries**: Structured notes including Executive Summary, Key Discussion Points, Confirmed Decisions, Action Items table (Task, Owner, Deadline, Evidence), and Risks/Open Questions. Copy to clipboard in 1 click for Notion, Obsidian, Slack, or Docs.
- ⚙️ **Configurable AI Models**: Switch between Whisper models (`tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`) and Ollama models with customizable system prompts.

---

## 📦 Installation Options

### Option 1: Debian/Ubuntu Package (`.deb`) — Recommended for Ubuntu, Debian, Mint, Pop!_OS

Download the `.deb` file from the [GitHub Releases](https://github.com/johnnyrockoff/briefly/releases) tab and install:
```bash
sudo dpkg -i briefly_1.0.0_all.deb
sudo apt-get install -f   # Installs missing system dependencies if needed
```
Launch **Briefly** from your application menu or run `briefly` in your terminal.

---

### Option 2: Universal Linux Installer (`install.sh`)

Works on any Linux distribution (Fedora, Arch Linux, openSUSE, etc.) without requiring root:
```bash
git clone https://github.com/johnnyrockoff/briefly.git
cd briefly
./install.sh
```

---

### Option 3: Run Directly from Source

```bash
git clone https://github.com/johnnyrockoff/briefly.git
cd briefly

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Briefly
./run_app.sh
```

---

## 🔧 Prerequisites

1. **FFmpeg** (required for audio capture):
   ```bash
   # Ubuntu / Debian
   sudo apt install ffmpeg

   # Fedora
   sudo dnf install ffmpeg

   # Arch Linux
   sudo pacman -S ffmpeg
   ```

2. **Ollama** (for local AI meeting summaries):
   Install [Ollama](https://ollama.ai) and pull the recommended model:
   ```bash
   ollama run qwen2.5:7b
   ```

---

## 🛠️ Building Release Packages

To compile installation packages for GitHub Releases:

### Build Debian (`.deb`) Package:
```bash
./scripts/build_deb.sh 1.0.0
# Outputs: dist/briefly_1.0.0_all.deb
```

### Build Portable (`.tar.gz`) Package:
```bash
./scripts/build_tarball.sh 1.0.0
# Outputs: dist/briefly-1.0.0-linux-portable.tar.gz
```

---

## 🧪 Running Tests

Run the automated test suite with pytest:
```bash
pytest
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
