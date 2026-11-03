from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
from jarvis.core.config import Settings
from jarvis.hardware.monitor import HardwareMonitor

class AIProvider(ABC):
    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def chat(self, prompt: str) -> str: ...

class LocalAIProvider(AIProvider):
    """Local quantized LLM provider backed by Ollama."""

    def __init__(self, settings: Settings, monitor: HardwareMonitor):
        self.settings = settings
        self.monitor = monitor

    def available(self) -> bool:
        try:
            r = requests.get(f"{self.settings.local_url}/api/tags", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def chat(self, prompt: str) -> str:
        h = self.monitor.snapshot()
        # Protect system resources: don't exhaust RAM/VRAM
        if h.ram_percent >= 90 or (h.vram_total_gb and (h.vram_used_gb or 0) / h.vram_total_gb >= 0.90):
            return "Local AI paused: System memory is over 90% utilization to prevent desktop slowdown."

        system_instruction = (
            "You are J.A.R.V.I.S., an intelligent and concise Windows AI desktop assistant. "
            "Provide helpful, direct, and well-structured answers without fluff."
        )

        try:
            # Try chat API first
            res = requests.post(
                f"{self.settings.local_url}/api/chat",
                json={
                    "model": self.settings.local_model,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                },
                timeout=45
            )
            if res.ok:
                data = res.json()
                msg = data.get("message", {}).get("content", "").strip()
                if msg:
                    return msg

            # Fallback to generate endpoint
            res_gen = requests.post(
                f"{self.settings.local_url}/api/generate",
                json={
                    "model": self.settings.local_model,
                    "prompt": f"{system_instruction}\n\nUser: {prompt}\nJARVIS:",
                    "stream": False
                },
                timeout=45
            )
            if res_gen.ok:
                return res_gen.json().get("response", "").strip()

            return f"Local Ollama responded with HTTP {res.status_code}."
        except requests.exceptions.Timeout:
            return "Local AI generation timed out. The local model is currently processing other tasks."
        except Exception as exc:
            return f"Local AI generation error: {exc}"

class CloudAIProvider(AIProvider):
    """Cloud AI provider supporting OpenAI API."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def available(self) -> bool:
        return bool(self.settings.cloud_api_key and self.settings.cloud_api_key.strip().startswith("sk-"))

    def chat(self, prompt: str) -> str:
        if not self.available():
            raise ValueError("No valid Cloud AI API key configured.")

        headers = {
            "Authorization": f"Bearer {self.settings.cloud_api_key.strip()}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.settings.cloud_model if self.settings.cloud_model else "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are J.A.R.V.I.S., a sophisticated AI desktop assistant. Answer clearly, accurately, and politely."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            if not response.ok:
                if response.status_code == 429:
                    raise RuntimeError("Cloud AI quota exceeded (Rate Limit 429).")
                elif response.status_code == 401:
                    raise RuntimeError("Cloud AI authorization failed (Invalid API key).")
                else:
                    raise RuntimeError(f"Cloud AI error (HTTP {response.status_code}): {response.text[:200]}")

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            raise

class CompositeAI:
    """Intelligent fallback coordinator across Cloud, Local Ollama, and offline modes."""

    def __init__(self, local_provider: LocalAIProvider, cloud_provider: CloudAIProvider, settings: Settings):
        self.local = local_provider
        self.cloud = cloud_provider
        self.settings = settings

    def query(self, prompt: str) -> str:
        mode = self.settings.ai_mode.lower()

        # 1. If configured explicitly for Cloud or Auto
        if mode in {"cloud", "auto"} and self.cloud.available():
            try:
                return self.cloud.chat(prompt)
            except Exception as e:
                logging.info(f"Cloud AI unavailable ({e}), automatically falling back to Local Ollama.")

        # 2. Local Ollama Provider
        if self.local.available():
            try:
                return self.local.chat(prompt)
            except Exception as e:
                logging.warning(f"Local AI encountered issue: {e}")

        # 3. Informative Local Knowledge Mode
        return (
            "I have processed your query in offline mode.\n\n"
            f"Query: '{prompt}'\n\n"
            "Status: Cloud AI is unconfigured or rate-limited, and local Ollama is standing by. "
            "To activate full conversational answers, run 'ollama run qwen2.5:3b' or provide a cloud API key in .env."
        )
