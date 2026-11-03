# J.A.R.V.I.S. Architecture Documentation

## 1. System Overview

J.A.R.V.I.S. is an offline-first Windows AI desktop assistant engineered in Python and PySide6. It is designed to bridge natural language understanding directly to deterministic, audited Windows automation without granting an LLM arbitrary shell access.

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      J.A.R.V.I.S. PySide6 Dashboard                   │
 │   [Arc Reactor Core]   [Hardware Telemetry]   [Command & Audio Audit]  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ User Input (Text / Voice STT)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │            Natural Language Understanding (NLU) Engine                 │
 │   - Intent Classification (Regex + Semantic Grammar)                   │
 │   - Entity & Parameter Extraction (Paths, Extensions, Applications)     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Parsed Directive
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                         Command Router                                 │
 ├───────────────────────────────────┬────────────────────────────────────┤
 │ Deterministic Tool Directive      │ Conversational / Knowledge Query   │
 │                                   │                                    │
 │                ▼                  │                 ▼                  │
 │   ┌───────────────────────────┐   │   ┌────────────────────────────┐   │
 │   │       Tool Registry       │   │   │       Composite AI         │   │
 │   │  - open_app, close_app    │   │   │  1. Cloud AI (OpenAI API)  │   │
 │   │  - organize_desktop       │   │   │  2. Local AI (Ollama 3B)   │   │
 │   │  - find_files, create_file│   │   │  3. Offline Knowledge Mode │   │
 │   │  - system_status          │   │   └────────────────────────────┘   │
 │   └─────────────┬─────────────┘   │                                    │
 └─────────────────┼─────────────────┴────────────────────────────────────┘
                   │
                   ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                 Security Policy & Gatekeeper                           │
 │   - Approved Directory Containment (Desktop, Documents, Downloads)     │
 │   - Traversal Prevention & System Root Protection                      │
 │   - Approval Gate: MEDIUM/HIGH risk prompts user confirmation          │
 └─────────────────┬──────────────────────────────────────────────────────┘
                   │ Authorized Operations Only
                   ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                       Windows Desktop Subsystems                       │
 │  [Process Control]  [Filesystem Manager]  [Hardware Sensors (psutil)]  │
 └────────────────────────────────────────────────────────────────────────┘
```

## 2. Core Modules

### 2.1 Natural Language Understanding (`jarvis.core.nlu`)
- **Purpose**: Translates natural, unstructured user phrases into deterministic command structures.
- **Components**:
  - `Intent`: Enumeration of recognized directive categories (`OPEN_APP`, `CLOSE_APP`, `OPEN_URL`, `LIST_PROCESSES`, `FIND_FILES`, `CREATE_FOLDER`, `CREATE_FILE`, `ORGANIZE_DESKTOP`, `SYSTEM_STATUS`, `REMINDER`, `AI_CHAT`).
  - `NaturalLanguageParser`: Employs robust semantic pattern matching and token extraction. Does not rely on fragile static keyword equality.

### 2.2 Security & Containment (`jarvis.security.policy`)
- **Purpose**: Restricts all assistant operations to authorized user folders.
- **Safeguards**:
  - Strict directory whitelisting (User Desktop, Documents, Downloads, Project Root).
  - Explicit blocking of `C:\Windows`, `System32`, `Program Files`, and protected system resources.
  - Path resolution strictly checks `resolve()` and prevents relative traversal (`..`).

### 2.3 Tool Registry & Windows Control (`jarvis.tools`)
- **`open_application`**: Resolves applications against `config/applications.json` and standard Windows paths; launches detached non-blocking processes.
- **`close_application`**: Terminates user applications after safety confirmation; explicitly prohibits terminating core Windows processes (`explorer.exe`, `svchost.exe`, etc.).
- **`organize_desktop`**:
  - *Phase 1 (Preview)*: Scans the user desktop, categorizes unorganized files by extension, proposes a structured destination schema, and prompts the user for approval.
  - *Phase 2 (Execute)*: Moves files into categorized folders (`Organized_Files/<Category>`), resolves naming collisions automatically, and provides an audited summary.
- **`find_files` & `create_file`**: Safe file operations with overwrite protection.

### 2.4 Hybrid AI Engine (`jarvis.ai.providers`)
- **Priority Tier**:
  1. **Cloud AI**: Used if an OpenAI API key is supplied in `.env`.
  2. **Local Ollama AI**: Quantized local model (`qwen2.5:3b`) running on `localhost:11434` with hardware resource guards.
  3. **Offline Knowledge Mode**: Fallback structured response if both providers are unavailable or offline.

### 2.5 Reactive User Interface (`jarvis.ui.dashboard`)
- Built with **PySide6 (Qt)**.
- Features code-drawn animated **Arc Reactor Core** with dynamic states (`IDLE`, `THINKING`, `SPEAKING`, `EXECUTING`, `ERROR`).
- Real-time 1 Hz hardware telemetry gauges (CPU, RAM, GPU, Power).
- Interactive **Approval Banner**: displays proposed operations requiring confirmation and provides single-click `[APPROVE]` and `[CANCEL]` buttons.
- Multi-threaded worker queue with lifetime tracking to eliminate Shiboken garbage-collection crashes.
