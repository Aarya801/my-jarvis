from __future__ import annotations
import json
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

from jarvis.core.config import load_settings
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.hardware.monitor import HardwareMonitor
from jarvis.ai.providers import LocalAIProvider, CloudAIProvider
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.system_tools import register_system_tools
from jarvis.core.router import CommandRouter
from jarvis.ui.dashboard import Dashboard
from jarvis.core.runtime import configure_logging
from jarvis.vision.screen import ScreenVision
from jarvis.integrations.web_research import WebResearch

class JarvisApp:
    def __init__(self):
        self.settings = load_settings()
        configure_logging(self.settings.root)
        logging.info("Starting J.A.R.V.I.S. Desktop Assistant")

        self.monitor = HardwareMonitor()
        self.memory = MemoryStore(self.settings.root / "data" / "jarvis.db")
        self.policy = SecurityPolicy(root=self.settings.root, private_mode=self.settings.privacy_mode)
        self.permission_mgr = PermissionManager(self.policy)
        self.registry = ToolRegistry(self.permission_mgr, self.memory)

        apps_config_path = self.settings.root / "config" / "applications.json"
        apps = {}
        if apps_config_path.exists():
            with open(apps_config_path, encoding="utf-8-sig") as f:
                apps = json.load(f)

        register_system_tools(self.registry, self.policy, apps)

        self.vision = ScreenVision(self.settings.root, self.settings.local_url, self.settings.vision_model)
        self.web = WebResearch()
        self.local_ai = LocalAIProvider(self.settings, self.monitor)
        self.cloud_ai = CloudAIProvider(self.settings)

        self.router = CommandRouter(
            registry=self.registry,
            memory=self.memory,
            local_ai=self.local_ai,
            cloud_ai=self.cloud_ai,
            settings=self.settings,
            vision=self.vision,
            web=self.web
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    jarvis_app = JarvisApp()
    window = Dashboard(jarvis_app)
    window.show()
    sys.exit(app.exec())
