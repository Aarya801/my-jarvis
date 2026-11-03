# J.A.R.V.I.S. Security & Safety Model

## 1. Principles of Least Privilege and Containment

Unlike naive "AI agent" architectures that feed shell execution strings directly from LLM completions into `subprocess.run(shell=True)`, J.A.R.V.I.S. enforces a **closed, allowlisted execution model**.

1. **No Arbitrary Code/Shell Execution**: An LLM cannot execute command line strings, scripts, or system-altering binaries directly.
2. **Deterministic Tool Registration**: Only tools formally registered in `ToolRegistry` can be invoked.
3. **Strict Path Containment**:
   - File reads, writes, searches, and moves are confined strictly to approved user workspaces:
     - User Desktop (`~/Desktop` or `~/OneDrive/Desktop`)
     - User Documents (`~/Documents`)
     - User Downloads (`~/Downloads`)
     - Project root
   - Any path resolving to `C:\Windows`, `C:\Program Files`, `C:\ProgramData`, or sensitive user directories (`.ssh`, `.aws`, `AppData`) raises an immediate `PermissionError`.
4. **No Silent Destruction**:
   - Overwriting existing files during file creation is strictly rejected.
   - Deleting files is not enabled in standard operations.
   - Relocating desktop files requires explicit confirmation.
5. **Protected System Processes**:
   - The application termination tool explicitly denies attempts to terminate critical Windows operating system tasks (`explorer.exe`, `svchost.exe`, `csrss.exe`, `dwm.exe`, `lsass.exe`, `services.exe`, etc.).
6. **Audit Trail**:
   - Every executed tool directive is permanently logged to `data/jarvis.db` in the SQLite audit table, recording the timestamp, tool name, parameters, risk tier, approval state, and result message.
7. **Privacy Mode**:
   - When `PRIVACY_MODE=true` is set in `.env`, all outbound network requests (cloud AI queries, web research, screen analysis APIs) are blocked.
