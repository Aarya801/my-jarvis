from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
def _bool(value: str) -> bool: return value.strip().lower() in {"1", "true", "yes", "on"}
@dataclass(frozen=True)
class Settings:
    root: Path; ai_mode: str; local_provider: str; local_url: str; local_model: str; cloud_provider: str; cloud_api_key: str; cloud_model: str; privacy_mode: bool; performance_mode: str; tts_enabled: bool; stt_enabled: bool; memory_enabled: bool; vision_model: str; voice_enabled: bool
def load_settings(root: Path = ROOT) -> Settings:
    load_dotenv(root / ".env")
    return Settings(root, os.getenv("AI_MODE", "auto").lower(), os.getenv("LOCAL_AI_PROVIDER", "ollama").lower(), os.getenv("LOCAL_AI_URL", "http://localhost:11434"), os.getenv("LOCAL_AI_MODEL", "qwen2.5:3b"), os.getenv("CLOUD_AI_PROVIDER", "openai").lower(), os.getenv("CLOUD_AI_API_KEY", ""), os.getenv("CLOUD_AI_MODEL", "gpt-5"), _bool(os.getenv("PRIVACY_MODE", "false")), os.getenv("PERFORMANCE_MODE", "balanced").lower(), _bool(os.getenv("TTS_ENABLED", "true")), _bool(os.getenv("STT_ENABLED", "false")), _bool(os.getenv("MEMORY_ENABLED", "false")), os.getenv("VISION_MODEL", ""), _bool(os.getenv("VOICE_ENABLED", "true")))
