# Manual Test Matrix

Because the front end depends on browser APIs and the Perchance runtime, the core test plan is browser/manual rather than a fake automated test suite.

| Area | Test | Expected result |
|---|---|---|
| Boot | Open the Perchance page | Boot sequence completes and dashboard appears |
| Chat | Send a normal question | J.A.R.V.I.S. replies without a page reload |
| Voice | Toggle voice and speak | Recognition starts/stops when browser supports it |
| Memory | `remember that I like X` | Memory appears and survives reload |
| Tasks | Add and remove a task | Task list updates and persists |
| UI | Change theme/accent | UI change persists after reload |
| Forge | Forge a small UI feature | Feature is installed and listed |
| Files | Open a local text file | File contents appear in editor |
| Save | Edit and save a local file | Updated contents are written/downloaded |
| Bridge | Launch bridge and connect | Status changes to direct PC link |
| Read | Read a known text file through bridge | Correct file contents are returned |
| Write | Write a test file through bridge | File is created/updated |
| Run | Run `echo hello` | Output is returned |
| Timeout | Run a command that exceeds the limit | Bridge terminates the request after timeout |
| Disconnect | Stop bridge | App reports that direct PC access is unavailable |
| Responsive UI | Test desktop + narrow browser | Panels remain usable without horizontal overflow |

## Release checklist

- [ ] No secrets or bridge token are committed.
- [ ] README setup steps match the current files.
- [ ] The Perchance page URL in the README is current.
- [ ] Bridge remains loopback-only.
- [ ] A harmless bridge command succeeds.
- [ ] Memory and tasks survive a reload.
- [ ] Browser console has no blocking errors during the normal flow.
