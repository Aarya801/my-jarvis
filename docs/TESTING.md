# J.A.R.V.I.S. Automated Test Documentation

## 1. Test Suite Overview

The automated test suite runs under `pytest` and verifies that every major layer of J.A.R.V.I.S. functions reliably without relying on mocks for local file semantics:

- **`test_audit_critical.py`**: Verifies path traversal attacks, system directory protection, protected process termination blocks, file overwrite guards, operation cancellation, and Ollama offline fallback handling.
- **`test_nlu.py`**: Verifies natural language intent parsing and entity extraction across all standard prompt directive patterns.
- **`test_policy.py`**: Verifies path containment, system directory blocks, path traversal rejection, and risk level policies.
- **`test_system_tools.py`**: Verifies folder creation, file creation, silent overwrite prevention, safe file copying, renaming, and multi-folder file search using temporary isolated directories (`tmp_path`).
- **`test_desktop_organizer.py`**: Verifies the two-stage Desktop Organizer workflow (Phase 1 Preview + Phase 2 Execution) in a mock desktop directory, verifying category mapping and file preservation.
- **`test_router.py`**: Verifies end-to-end command routing, greeting dispatch, hardware status queries, protected process blocks, and approval replay.
- **`test_core.py`**: Verifies configuration parsing, SQLite memory store round-trip, and tool audit logging.

## 2. Running Tests

To run the full suite:

```powershell
.venv\Scripts\activate
python -m pytest -v
```

Expected output: `28 passed in ~2.5s`.
