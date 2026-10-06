# Security Notes

J.A.R.V.I.S. has a local PC-control bridge, so security is treated as a feature rather than an afterthought.

## Trust boundary

The browser application is untrusted relative to the Windows machine. The PowerShell bridge is the privileged boundary.

### Controls

- Bridge listens only on `127.0.0.1`.
- Privileged endpoints require `X-Token`.
- The token is generated and stored locally in the user's profile.
- `/status` does not expose the token and is used only as a connectivity probe.
- Command execution has a 30-second timeout.
- Command output is capped before returning to the browser.
- The bridge window indicates that closing it removes direct PC access.

## Important limitation

A token-authenticated local shell bridge is still a powerful capability. This project is intended for the owner's personal Windows machine, not for exposing the bridge to the internet or a shared network.

Never port-forward `8765`, bind the listener to `0.0.0.0`, commit the token file, or paste the token into source code.

## Recommended operating model

1. Run the bridge only when PC-control features are needed.
2. Keep the bridge on loopback.
3. Treat the token like a password.
4. Review commands before allowing destructive operations.
5. Stop the bridge when finished.

The project describes the bridge as **local PC control**, not as a secure remote administration product.
