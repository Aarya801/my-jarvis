# J.A.R.V.I.S. Architecture

J.A.R.V.I.S. is intentionally built as a lightweight client + local bridge system rather than a single monolithic desktop executable.

```text
Web app (index.html) -> Perchance AI + KV persistence
                         |
                         | HTTP + X-Token
                         v
                  Local PowerShell bridge
                    127.0.0.1:8765
                         |
                  Filesystem / cmd.exe
```

## Responsibilities

### Web application
- Presents the J.A.R.V.I.S. interface and visual system dashboard.
- Handles text and browser speech recognition/synthesis when supported.
- Uses the Perchance AI text generator for natural-language replies and command interpretation.
- Persists user memory, tasks, and UI evolution through the Perchance key-value plugin.
- Uses the browser File System Access API when available, with a file-input/download fallback.
- Talks to the bridge only when the user explicitly connects it.

### Local bridge
- Binds to loopback (`127.0.0.1`) rather than a LAN interface.
- Uses a locally stored token for privileged requests.
- Exposes a deliberately small API: status, directory listing, read, write, and command execution.
- Limits command execution to 30 seconds and truncates oversized output.

## Data flow

1. User enters a natural-language request.
2. J.A.R.V.I.S. first checks deterministic local commands.
3. If needed, the AI interpreter maps natural language to a canonical command.
4. File/PC operations are sent to the local bridge with `X-Token` authentication.
5. The result is fed back into the response context so the assistant reports the actual outcome rather than inventing one.
6. Memory and UI changes are persisted separately.

## Design decisions

- **Progressive enhancement:** the assistant remains useful without the bridge.
- **Local-first PC control:** privileged Windows access stays on the user's machine.
- **Small protocol surface:** fewer endpoints make the bridge easier to understand and audit.
- **Deterministic before generative:** common commands are handled locally to reduce latency and accidental interpretation.
- **Explainable structure:** the project is intentionally small enough for a first-year student to explain component-by-component.
