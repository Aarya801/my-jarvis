# J.A.R.V.I.S. Setup

## Current Python desktop application

The current `main.py` starts the Windows desktop application built with Python and PySide6.

### Requirements

- Windows 10 or 11 (the automation tools are Windows-oriented)
- Python 3.10 or newer
- Optional: Ollama and the `qwen2.5:3b` model for local language-model responses
- Optional: credentials for a configured cloud AI provider

### Install and run

From PowerShell in the repository directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Configure optional provider and privacy settings in `.env` as described by the example file. Do not commit API keys.
The local AI provider requires Ollama to be installed and running; pull the model with `ollama run qwen2.5:3b`.
Without a local model or configured cloud provider, the application can use its offline fallback behavior.

### Run tests

```powershell
python -m pytest -v
```

The tests use isolated temporary paths for filesystem operations. They do not establish that every Windows integration
works on every PC; verify the relevant features on the target Windows version and hardware.

## Legacy browser prototype

The repository also retains `index.html` and `main.pjs`, an earlier Perchance browser prototype, plus an optional
PowerShell bridge under `src/`. This is separate from the current Python desktop application. Browser speech and File
System Access APIs vary by browser. The bridge exposes sensitive local actions; keep it bound to loopback and do not
expose it to a public or shared network. Its legacy flow is not the setup path for the current desktop app.
