"""Explicit, one-shot screen capture and optional Ollama vision analysis."""
from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
import requests
from PySide6.QtGui import QGuiApplication


class ScreenVision:
    def __init__(self, root: Path, local_url: str, model: str):
        self.root, self.local_url, self.model = root, local_url.rstrip("/"), model.strip()

    def capture(self) -> Path:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("No desktop screen is available to capture.")
        folder = self.root / "data" / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"screen-{datetime.now():%Y%m%d-%H%M%S}.png"
        if not screen.grabWindow(0).save(str(target), "PNG"):
            raise RuntimeError("Windows denied the screen capture.")
        return target

    def analyze(self, prompt: str) -> tuple[Path, str]:
        image = self.capture()
        if not self.model:
            return image, "I captured the current screen. Configure VISION_MODEL with an Ollama vision model (for example a lightweight LLaVA-compatible model) to have me describe it."
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        payload = {"model": self.model, "prompt": prompt or "Describe what is visible on this screen clearly and concisely.", "images": [encoded], "stream": False}
        try:
            response = requests.post(f"{self.local_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            return image, answer or "The configured vision model returned no description."
        except requests.RequestException as exc:
            return image, f"I captured the screen, but vision analysis could not run: {exc}. Check that Ollama and VISION_MODEL are configured."
