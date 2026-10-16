# 🎙️ Briefly

[![Latest Release](https://img.shields.io/github/v/release/johnnyrockoff/briefly?color=0078D6&label=Latest%20Release&logo=github)](https://github.com/johnnyrockoff/briefly/releases/latest)
[![Linux](https://img.shields.io/badge/OS-Linux-FCC624?logo=linux&logoColor=black)](https://github.com)
[![Windows](https://img.shields.io/badge/OS-Windows%2010%2F11-0078D6?logo=windows&logoColor=white)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Qt6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?logo=qt&logoColor=white)](https://qt.io)
[![Whisper](https://img.shields.io/badge/AI-OpenAI%20Whisper-brightgreen)](https://github.com/openai/whisper)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20Local-orange)](https://ollama.ai)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Briefly** is an intelligent, privacy-first cross-platform desktop app for **Linux** and **Windows** that records online meetings (capturing both other participants and your microphone), generates high-fidelity offline transcriptions with **OpenAI Whisper**, and crafts structured executive summaries using local LLMs via **Ollama**.

---

## 📥 Instant Downloads (1-Click)

Click below to download the latest stable release for your operating system (links always point to the newest version automatically):

| Operating System | Package Format | Architecture | Direct Download |
| :--- | :--- | :---: | :---: |
| 🪟 **Windows 10 / 11** | Portable ZIP (`Briefly.exe`) | 64-bit | [⬇️ **Download Briefly for Windows**](https://github.com/johnnyrockoff/briefly/releases/latest/download/briefly-windows-portable.zip) |
| 🐧 **Ubuntu / Debian / Mint** | Debian Installer (`.deb`) | Universal | [⬇️ **Download .deb Package**](https://github.com/johnnyrockoff/briefly/releases/latest/download/briefly-linux.deb) |
| 🐧 **Universal Linux** (Fedora / Arch) | Portable Bundle (`.tar.gz`) | 64-bit | [⬇️ **Download .tar.gz Bundle**](https://github.com/johnnyrockoff/briefly/releases/latest/download/briefly-linux-portable.tar.gz) |

> 💡 *Need a continuous nightly build or older versions? View all releases on the [GitHub Releases page](https://github.com/johnnyrockoff/briefly/releases).*

---

## ✨ Features

- 🎧 **Smart Audio Mixing & Dynamic Normalization**: 
  - **Linux**: Captures system monitor/headphones & microphone via PulseAudio / PipeWire.
  - **Windows**: Captures speaker/headphone output via native **WASAPI Loopback** & microphone without requiring Stereo Mix or virtual audio cables.
  - **Dynamic Audio Normalization (`dynaudnorm` + `alimiter`)**: Automatically balances quiet remote speakers and local microphone levels into a clean, normalized 16 kHz mono stream.
- ⚡ **Whisper Turbo & High-Fidelity Decoding**:
  - GPU-accelerated speech recognition powered by OpenAI's **Whisper Turbo** model.
  - **Beam Search Decoding** (`beam_size=5`, `best_of=5`) and hallucination suppression.
  - **Domain-Specific Vocabulary Prompting**: Pre-conditions Whisper with technical and corporate terminology (*deploy, sprint, pull request, pipeline, backlog*) and clear punctuation.
- 👥 **Neural Speaker Diarization (Multi-Speaker Attribution)**:
  - Automatically identifies and distinguishes different participants across the call (`[00:01:23] Interlocutor 1: ...`, `[00:01:45] Interlocutor 2: ...`).
  - Powered by offline neural voice clustering via **Sherpa-ONNX & 3D-Speaker** — 100% private, local, and requiring zero external API keys or tokens.
- 📂 **Custom Storage Directory**:
  - Full control over where meeting data is saved: choose any custom directory (local SSD, secondary drive, or synced folder like Nextcloud, Dropbox, or Google Drive) directly in Settings.
  - Automatically manages subfolders for `recordings/`, `transcripts/`, and `summaries/`.
- 🌐 **Multilingual Support (Input & Output)**:
  - **Spoken Language**: Auto-detection or explicit selection (English, Portuguese, Spanish, French, German, Italian, etc.) for Whisper speech-to-text.
  - **Summary Output**: Generate summaries natively translated into your preferred business language with localized section titles, action item tables, and executive terminology.
- 💻 **Hardware Profile & GPU Acceleration**:
  - Automatically detects **NVIDIA CUDA**, **AMD ROCm**, or **CPU / Integrated Graphics**.
  - Recommends optimal Whisper models (`turbo` for GPU, `base` for CPU) and Ollama models tailored to your machine's VRAM and RAM.
- 📥 **In-App 1-Click Dependency Installer**:
  - Missing FFmpeg? Download a portable static FFmpeg binary directly from the app without root/admin privileges.
  - Pull Ollama models with a live progress bar and transfer speed indicator directly in the diagnostics window.
- 🚀 **System Tray Daemon**: Start, pause, or stop recordings with a single click even when the window is hidden during Google Meet, Zoom, Teams, or Discord calls.
- 🩺 **Built-in System Diagnostics**: Automatic health check verifying audio devices, FFmpeg, PyTorch/GPU readiness, and Ollama service connectivity.
- 🔄 **Live History & File Synchronization**: Instantly syncs meeting records when files are removed, showing clean empty states when no recordings are present.
- 🔒 **100% Offline & Private**: Audio processing, transcription, and summarization never leave your machine — no subscriptions, no cloud uploads.
- 📋 **Executive Markdown Summaries**: Structured notes including Executive Summary, Key Discussion Points, Confirmed Decisions, Action Items table (Task, Owner, Deadline, Evidence), and Risks/Open Questions. Copy to clipboard in 1 click for Notion, Obsidian, Slack, or Docs.

---

## 📦 Installation & Setup

### 🪟 Windows (10 / 11)
1. Download [briefly-windows-portable.zip](https://github.com/johnnyrockoff/briefly/releases/latest/download/briefly-windows-portable.zip).
2. Extract the ZIP anywhere on your PC.
3. Double-click `Briefly.exe` to run.
*(On first launch, Briefly will detect if FFmpeg or Ollama are missing and offer to install/configure them with 1 click).*

---

### 🐧 Linux

#### Option 1: Debian/Ubuntu Package (`.deb`)
Recommended for Ubuntu, Debian, Linux Mint, Pop!_OS:
```bash
sudo dpkg -i briefly_*_all.deb
sudo apt-get install -f   # Installs system dependencies if needed
```
Launch **Briefly** from your application menu or run `briefly` in your terminal.

#### Option 2: Universal Linux Installer (`install.sh`)
Works on any Linux distribution (Fedora, Arch Linux, openSUSE, etc.) without requiring root:
```bash
git clone https://github.com/johnnyrockoff/briefly.git
cd briefly
./install.sh
```

#### Option 3: Run Directly from Source
```bash
git clone https://github.com/johnnyrockoff/briefly.git
cd briefly

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run Briefly
./run_app.sh                   # On Windows: python run.py
```

---

## 🔧 Prerequisites (Optional / Auto-installable)

Briefly can automatically configure its dependencies via the in-app **Health Check & Diagnostics** dialog:

1. **FFmpeg**: Handled automatically in-app, or install via system package manager:
   - Ubuntu / Debian: `sudo apt install ffmpeg`
   - Fedora: `sudo dnf install ffmpeg`
   - Arch Linux: `sudo pacman -S ffmpeg`
   - Windows: `winget install Gyan.FFmpeg`
2. **Ollama**:
   - Install from [ollama.ai](https://ollama.ai).
   - Briefly will detect Ollama and allow pulling recommended models (`qwen2.5:7b`, `llama3.2`, etc.) directly from the UI.

---

## 🛠️ Building Release Packages

### Windows Standalone Executable (`.exe`):
On Windows with Python 3.10+:
```bat
scripts\build_windows.bat
:: Outputs: dist\Briefly\Briefly.exe and dist\briefly-*-windows-portable.zip
```

### Linux Debian (`.deb`) Package:
```bash
./scripts/build_deb.sh 1.0.0
# Outputs: dist/briefly_1.0.0_all.deb
```

### Linux Portable (`.tar.gz`) Package:
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
