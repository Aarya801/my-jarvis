"""Opt-in, single-shot microphone transcription for JARVIS push-to-talk."""
from __future__ import annotations
import logging

class VoiceCommand:
    def listen_once(self) -> str:
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise RuntimeError("Voice recognition dependency missing. Install: pip install SpeechRecognition") from exc

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
            # Cloud STT recognition on speech audio
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            raise RuntimeError("No speech detected within listening window.")
        except sr.UnknownValueError:
            raise RuntimeError("Audio was received, but speech could not be recognized.")
        except sr.RequestError as exc:
            raise RuntimeError(f"Speech recognition service unreachable: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Microphone access error: {exc}")
