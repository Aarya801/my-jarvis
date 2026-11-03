# J.A.R.V.I.S. 2.0 — Windows AI Desktop Assistant

> **A professional, local-first Windows AI desktop assistant combining PySide6 HUD telemetry, deterministic natural-language desktop automation, local Ollama LLM integration, and strict security sandboxing.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/UI-PySide6%20(Qt)-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![AI Engine](https://img.shields.io/badge/Local%20AI-Ollama%20(qwen2.5%3A3b)-black?style=for-the-badge)](https://ollama.com/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed-brightgreen?style=for-the-badge)](docs/TESTING.md)

---

> ### ⚠️ Project Scope & Security Disclaimer
> **J.A.R.V.I.S. is a local, sandboxed Windows desktop assistant and NOT an unrestricted autonomous agent.**
> - It operates strictly within allowlisted user directories (`Desktop`, `Documents`, `Downloads`, Project Root).
> - It does NOT possess arbitrary shell execution privileges, cannot run raw LLM-generated bash/cmd scripts, and cannot modify Windows system files or terminate protected operating system processes.
> - High-risk actions (desktop reorganization, file moves, process termination) require explicit, interactive human confirmation via the dashboard.

---

## 🚀 Overview

**J.A.R.V.I.S. (Just A Rather Very Intelligent System)** is an engineering-grade personal desktop assistant designed for Windows 10/11. Unlike basic chatbot wrappers, J.A.R.V.I.S. integrates **real operating system control**—launching applications, organizing files, monitoring hardware, and parsing natural language directives—while strictly enforcing a **least-privilege safety boundary** that prevents destructive actions or arbitrary shell execution.

Built for standard consumer laptops (tested on Intel Core i5 / 16 GB RAM / NVIDIA RTX 3050 Laptop GPU), J.A.R.V.I.S. operates offline-first using local quantized models, falling back to structured responses or optional cloud AI when configured.

---

## ⚡ Key Working Features

### 🖥️ 1. Real Windows Desktop Automation
- **Application Control**: Intelligently launches installed Windows applications (`Chrome`, `VS Code`, `Notepad`, `Calculator`, `File Explorer`, `Terminal`, `Task Manager`) with detached processes so the UI never freezes.
- **Process Management**: Lists active user applications with PIDs and memory usage in a structured table; closes target user processes with explicit confirmation while strictly protecting Windows core processes (`explorer.exe`, `svchost.exe`, `dwm.exe`, `csrss.exe`, etc.).
- **Web Navigation**: Opens websites and common destinations (`YouTube`, `GitHub`, `StackOverflow`, `Google`, `Reddit`, custom URLs) in your default browser.

### 📁 2. File & Directory Management
- **Smart File Search**: Recursively searches across user folders (`Desktop`, `Documents`, `Downloads`, Project Root) by keyword or extension (`.py`, `.pdf`, `.docx`, `.xlsx`, `.zip`, etc.) with file size previews.
- **Folder & Note Creation**: Creates directories and text notes in approved locations without manual path configuration.
- **Safety Overwrite Protection**: Prohibits silently overwriting existing files; validates paths against directory traversal (`..`).

### 🧹 3. Desktop Organization with Preview & Confirmation
Say *"JARVIS, organize my desktop"* and watch it:
1. Scan your desktop (handles OneDrive Desktop and native Desktop).
2. Categorize files into organized buckets: `Documents`, `Images`, `Code_Development`, `Archives`, `Installers`, `Media`.
3. Generate a **structured preview proposal** detailing all proposed moves.
4. Prompt for your **explicit interactive confirmation** via the UI approval banner.
5. On approval, safely relocates files into `Desktop/Organized_Files/<Category>/` with collision resolution (never deletes or overwrites).

### 🧠 4. Natural Language Command System (NLU)
No need to memorize exact command syntax. J.A.R.V.I.S. automatically extracts intent and parameters:
- *"Open Chrome"*
- *"Open YouTube"*
- *"Find my Python files"*
- *"Search my Downloads folder for PDFs"*
- *"Create a folder called College Projects on my desktop"*
- *"Make a new text file with today's study plan"*
- *"How much RAM am I using?"*
- *"What applications are currently running?"*
- *"Organize my desktop"*
- *"What time is it?"*

### 🎙️ 5. Push-to-Talk Voice Interaction
- Single-shot, user-controlled speech-to-text (Microphone is never continuously recording in the background).
- Text-to-speech spoken audio replies using Windows SAPI5 with COM thread isolation (`pythoncom.CoInitialize()`).
- Real-time animated audio visualizer strip on the dashboard.

### 📊 6. Real-Time Hardware Telemetry
- Animated 1 Hz live hardware monitors: CPU %, RAM used/total, System Disk free/total, Battery status, GPU Model, and VRAM.
- Dedicated hardware-aware safety guard: pauses resource-heavy local LLM generation if RAM exceeds 90% utilization.

### 🛡️ 7. Strict Security & Audit Logging
- **Containment Policy**: Confines all assistant file operations strictly to approved user directories; blocks `C:\Windows`, `C:\Program Files`, and system roots.
- **Interactive Approval Banner**: Medium/High risk operations (desktop reorganization, file moves, process termination) cannot proceed without explicit click authorization.
- **SQLite Audit Trail**: All directives, parameters, risk levels, and results are logged to `data/jarvis.db`.

---

## 🏛️ Architecture

```text
 ┌────────────────────────────────────────────────────────┐
 │            PySide6 Arc Reactor Command HUD             │
 │  [Arc Core Animation]  [Telemetry]  [Approval Banner]  │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │        Natural Language Understanding (NLU)            │
 │   - Semantic Pattern Matching & Entity Extraction      │
 └───────────────────────────┬────────────────────────────┘
                             │ Parsed Intent & Params
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                     Command Router                     │
 ├───────────────────────────┬────────────────────────────┤
 │ Deterministic Tool Calls  │ Conversational Q&A         │
 │            ▼              │             ▼              │
 │    [Tool Registry]        │      [Composite AI]        │
 │  - open_application       │  1. Cloud AI (OpenAI API)  │
 │  - organize_desktop       │  2. Local Ollama (qwen2.5) │
 │  - find_files, create_file│  3. Offline Knowledge Mode │
 └────────────┬──────────────┴────────────────────────────┘
              │
              ▼
 ┌────────────────────────────────────────────────────────┐
 │         Security Containment & Permission Gate         │
 │   - Approved Path Validator (traversal prevention)     │
 │   - Approval Gate: MEDIUM/HIGH risk prompts user       │
 └────────────┬───────────────────────────────────────────┘
              │ Authorized Operations Only
              ▼
 ┌────────────────────────────────────────────────────────┐
 │              Windows Operating System Host             │
 │   - Detached Process Execution                         │
 │   - Filesystem Relocations                             │
 │   - psutil Telemetry Sensors                           │
 └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Windows 10 or 11** (64-bit)
- **Python 3.10+** (Python 3.12 recommended)
- **Optional**: [Ollama](https://ollama.com/) for local offline LLM intelligence (`ollama run qwen2.5:3b`)

### Quick Setup

```powershell
# 1. Clone repository
git clone https://github.com/Aarya801/my-jarvis.git
cd my-jarvis

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
Copy-Item .env.example .env
```

### Running J.A.R.V.I.S.

Double-click `start_jarvis.bat` or run via terminal:

```powershell
python main.py
```

---

## 🧪 Testing

J.A.R.V.I.S. includes a comprehensive automated test suite with **28 tests** covering NLU parsing, file containment, security rules, desktop organization, Ollama fallbacks, overwrite protection, and command routing:

```powershell
python -m pytest -v
```

All file tests run inside isolated temporary directories (`tmp_path`) ensuring your real desktop and user files are never touched during automated testing.

---

## 🔒 Security Guarantees & Known Limitations

### Security Guarantees
- J.A.R.V.I.S. will **never** execute arbitrary shell commands directly from LLM output.
- J.A.R.V.I.S. will **never** silently overwrite or delete your personal files.
- J.A.R.V.I.S. will **never** access browser cookies, saved passwords, or private authentication tokens.
- All high-risk actions require interactive one-click approval on the dashboard.

### Known Limitations
- **Push-to-Talk Only**: Voice input requires deliberate push-to-talk by design; an always-on continuous room microphone listener is deliberately omitted for privacy.
- **Vision Model**: Screen captures are saved locally; answering questions about screen contents requires pulling an Ollama vision model (`ollama run llava`).
- **Document RAG**: Large document indexing and vector database search are architectural next steps, not current features.

---

## 👨‍💻 Developer & Portfolio Info

- **Developer**: Aarya (CSE First-Year Student)
- **Focus Areas**: Software Architecture, Windows Systems Engineering, UI/UX Design (Qt/PySide6), AI/NLU Integration, Cybersecurity & Principle of Least Privilege.
