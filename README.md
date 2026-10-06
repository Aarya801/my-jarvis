# J.A.R.V.I.S. — Personal AI Assistant

> **A browser-based personal AI assistant with voice interaction, persistent memory, self-extending UI features, and an optional local Windows control bridge.**

[![Platform](https://img.shields.io/badge/platform-Web%20%2B%20Windows-00d4ff?style=for-the-badge)](https://perchance.org/my-jarvis)
[![AI](https://img.shields.io/badge/AI-Perchance%20AI-111827?style=for-the-badge)](https://perchance.org/my-jarvis)
[![Status](https://img.shields.io/badge/status-active%20personal%20project-00ff9d?style=for-the-badge)](https://github.com/Aarya801/my-jarvis)

J.A.R.V.I.S. is a personal engineering project built around a simple idea: **natural language should be able to control a useful personal workspace without hiding the underlying system.**

It combines a futuristic dashboard with practical software components: browser AI, speech APIs, persistent key-value storage, file editing, a local Windows bridge, command interpretation, and a small feature-forging system.

## ✨ What it can do

- 💬 **AI conversation** — natural-language chat through the Perchance AI runtime.
- 🎙️ **Voice interaction** — browser speech recognition and speech synthesis when supported.
- 🧠 **Persistent memory** — remembers user facts, preferences, and tasks.
- 🛠️ **Self-extending UI** — can forge, edit, list, and remove small persistent interface features.
- 💻 **Local PC bridge** — optional loopback-only Windows bridge for file operations and commands.
- 📁 **File workspace** — open, edit, save, list, read, and write text files.
- ⚡ **Command translation** — converts natural language into deterministic internal commands before execution.
- 🎛️ **Evolving interface** — themes, accents, buttons, protocols, system telemetry, and holographic UI effects.
- 📱 **Progressive web experience** — can be installed/opened as a standalone app where the browser supports it.

## 🧩 Architecture

```text
                    ┌─────────────────────────┐
                    │      J.A.R.V.I.S. UI    │
                    │       index.html        │
                    │                         │
                    │ Chat • Voice • Memory   │
                    │ Commands • Forge • UI  │
                    └────────────┬────────────┘
                                 │
                    Natural-language commands
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
   ┌────────────────────┐                ┌────────────────────┐
   │ Perchance runtime  │                │ Local PC bridge    │
   │ AI + KV persistence│                │ PowerShell         │
   └────────────────────┘                │ 127.0.0.1:8765     │
                                         └─────────┬──────────┘
                                                   │
                                      ┌────────────┴───────────┐
                                      │                        │
                                      ▼                        ▼
                                  Filesystem             Windows shell
```

The bridge is intentionally **optional**. Without it, the assistant still provides chat, memory, tasks, voice, UI evolution, and browser-based file operations.

## 📁 Project structure

```text
my-jarvis/
├── index.html                  # Main UI, assistant logic, voice and command layer
├── main.pjs                    # Perchance generator configuration/data
├── README.md                   # Project overview
├── LICENSE                     # MIT license
├── SECURITY.md                 # Security reporting policy
├── .gitignore                  # Local-secret/runtime exclusions
├── docs/
│   ├── ARCHITECTURE.md         # System design and data flow
│   ├── SECURITY.md             # Threat model and bridge safeguards
│   ├── SETUP.md                # Setup + troubleshooting
│   └── TESTING.md              # Manual release/test matrix
└── src/
    ├── JARVIS-App.bat          # Windows launcher
    ├── Stop-JARVIS-Bridge.bat  # Stops local bridge
    ├── jarvis-bridge.ps1       # Loopback PC-control service
    └── *.png                    # Holographic UI assets
```

## 🚀 Live version

**Perchance:** https://perchance.org/my-jarvis

The live page is the easiest way to explore the interface. The repository contains the source and local-bridge components needed to understand and reproduce the project.

## 🖥️ Run the Windows bridge

1. Open the J.A.R.V.I.S. web app.
2. Double-click `src/JARVIS-App.bat` on the same Windows PC.
3. Copy the displayed token.
4. Paste it into the app's **CONNECT** box.
5. Press **CONNECT**.
6. Close the bridge window when direct PC access is no longer needed.

See [`docs/SETUP.md`](docs/SETUP.md) for the full guide.

> ⚠️ The bridge provides powerful local PC capabilities. It is designed for personal use on the owner's machine and should **never** be exposed to the public internet or a shared network.

## 🔐 Engineering & security decisions

The project deliberately separates the public web UI from privileged local operations.

- Local bridge binds to `127.0.0.1`.
- Privileged bridge requests require an `X-Token`.
- Bridge command execution has a timeout and output cap.
- The token is stored locally rather than committed to Git.
- The bridge can be stopped independently of the web app.
- The browser app continues operating when the bridge is offline.

More detail: [`docs/SECURITY.md`](docs/SECURITY.md).

## 🧪 Testing

The browser/Perchance environment means a meaningful test strategy is primarily integration and manual testing rather than pretend unit tests around browser APIs.

The repository includes a release-oriented test matrix covering boot, chat, voice, memory, tasks, UI evolution, file access, bridge authentication, read/write operations, command execution, timeout behavior, and disconnect handling.

See [`docs/TESTING.md`](docs/TESTING.md).

## 🧠 What this project demonstrates

From a CSE perspective, the interesting part is not the J.A.R.V.I.S. theme. The project demonstrates several engineering concepts working together:

| Area | Demonstrated concept |
|---|---|
| Programming | State, functions, async operations, event-driven browser code |
| AI | Prompted generation + natural-language command interpretation |
| Systems | Browser ↔ local process communication |
| Networking | HTTP requests, loopback service, headers and authentication |
| Security | Trust boundaries, local token authentication, least exposure |
| Web development | Responsive UI, Web APIs, persistent state |
| Automation | File operations and controlled command execution |
| UX | Voice controls, feedback states, visual telemetry |
| Software engineering | Documentation, architecture, testing plan, modular responsibilities |

## 🛣️ Future roadmap

Potential next iterations:

- Replace the PowerShell bridge with a small typed local service.
- Add a permission model for individual PC capabilities.
- Add structured command schemas instead of free-form shell strings.
- Add automated browser smoke tests.
- Add plugin-style skill modules.
- Add local speech-to-text / text-to-speech options for offline operation.
- Add encrypted local memory for sensitive personal data.
- Add a proper event/audit log for PC actions.

## 👨‍💻 Project context

J.A.R.V.I.S. is a personal first-year CSE Core engineering project by **Aarya Lalan**.

The goal is not to reproduce a fictional AI character. The goal is to explore how **AI, web APIs, automation, local systems, and user interfaces can be combined into one explainable software system.**

---

**Project:** J.A.R.V.I.S.  
**Author:** Aarya Lalan  
**Live:** https://perchance.org/my-jarvis
