"""Thread-safe Windows Text-to-Speech engine using SAPI5."""
from __future__ import annotations
import logging

class VoiceOutput:
    def speak(self, text: str) -> None:
        if not text or not text.strip():
            return

        clean_text = text[:1500].strip()

        # COM initialization required on Windows worker threads
        has_pythoncom = False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            has_pythoncom = True
        except Exception:
            pass

        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 185)
            engine.setProperty("volume", 0.95)
            engine.say(clean_text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            logging.error(f"Text-to-speech error: {exc}")
        finally:
            if has_pythoncom:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
