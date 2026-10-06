# Setup Guide

## Web app

1. Open the J.A.R.V.I.S. generator on Perchance.
2. Paste/update `index.html` and `main.pjs`.
3. Save the generator.
4. Open the published page.

## Optional Windows bridge

1. Keep the repository on the Windows PC where PC control is needed.
2. Run `src/JARVIS-App.bat`.
3. Copy the displayed bridge token.
4. Paste it into the J.A.R.V.I.S. **CONNECT** box.
5. Press **CONNECT**.
6. Close the bridge window when direct PC access is no longer needed.

## Browser requirements

Chrome/Edge provide the best experience because J.A.R.V.I.S. can use Speech Recognition and the File System Access API when available. The app still has fallbacks for ordinary file input/download flows.

## Troubleshooting

### Bridge says offline

- Confirm the bridge window is running.
- Confirm it says `127.0.0.1:8765` and did not report `START FAILED`.
- Paste the token again and press **CONNECT**.

### Voice does not work

Browser speech APIs vary by browser and operating system. Use the text box if recognition is unavailable.

### PC control is unavailable

The bridge is intentionally optional. File editing through browser APIs and normal chat continue to work without it.
