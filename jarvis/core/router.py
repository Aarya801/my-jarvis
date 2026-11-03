from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jarvis.core.models import ToolResult, Risk
from jarvis.core.nlu import NaturalLanguageParser, Intent, ParsedCommand
from jarvis.core.config import Settings
from jarvis.tools.registry import ToolRegistry
from jarvis.memory.store import MemoryStore
from jarvis.ai.providers import CompositeAI, LocalAIProvider, CloudAIProvider
from jarvis.vision.screen import ScreenVision
from jarvis.integrations.web_research import WebResearch

class CommandRouter:
    """Intelligent command router dispatching natural language to audited tools or AI."""

    def __init__(
        self,
        registry: ToolRegistry,
        memory: MemoryStore,
        local_ai: LocalAIProvider,
        cloud_ai: CloudAIProvider,
        settings: Settings,
        vision: Optional[ScreenVision] = None,
        web: Optional[WebResearch] = None
    ):
        self.registry = registry
        self.memory = memory
        self.local_ai = local_ai
        self.cloud_ai = cloud_ai
        self.settings = settings
        self.vision = vision
        self.web = web
        self.parser = NaturalLanguageParser()
        self.ai = CompositeAI(local_ai, cloud_ai, settings)

    def handle(self, text: str, approved: bool = False, pending_action: Optional[Dict[str, Any]] = None) -> ToolResult:
        # If this is an explicit confirmation replay of a pending action
        if approved and pending_action:
            tool_name = pending_action.get("tool_name")
            kwargs = pending_action.get("kwargs", {})
            if tool_name:
                return self.registry.run(tool_name, approved=True, **kwargs)

        q = text.strip()
        if not q:
            return ToolResult(False, "Directive cannot be empty.")

        # Parse command with NLU engine
        parsed: ParsedCommand = self.parser.parse(q)

        # 1. Greeting
        if parsed.intent == Intent.GREETING:
            return ToolResult(
                True,
                "Greetings. I am J.A.R.V.I.S., your Windows desktop assistant. "
                "All systems are online, telemetry is nominal, and safety containment is active. "
                "How may I assist you today?"
            )

        # 2. Screen Vision
        if parsed.intent == Intent.SCREEN_VISION:
            if self.settings.privacy_mode:
                return ToolResult(False, "Private Mode is active: Screen analysis is disabled to protect local privacy.")
            if not self.vision:
                return ToolResult(False, "Screen capture module is not initialized.")
            try:
                image_path, answer = self.vision.analyze(q)
                return ToolResult(True, f"Screen Analysis Complete:\n{answer}", {"screenshot": str(image_path)})
            except Exception as e:
                return ToolResult(False, f"Screen analysis encountered an error: {e}")

        # 3. Reminder & Memory
        if parsed.intent == Intent.REMINDER:
            content = parsed.params.get("content", q)
            due_at = (datetime.now() + timedelta(hours=1)).isoformat()
            self.memory.add_reminder(content, due_at)
            return ToolResult(True, f"Reminder recorded: '{content}' (Scheduled for review).")

        # 4. Tool Directives (Application control, files, desktop organize, system status)
        if parsed.tool_name:
            tool_res = self.registry.run(parsed.tool_name, approved=approved, **parsed.params)
            # If the tool succeeded or requires confirmation, return immediately
            if tool_res.ok or tool_res.requires_confirmation:
                return tool_res
            # If application not found or specific tool error, return error
            if parsed.intent in {Intent.OPEN_APP, Intent.CLOSE_APP, Intent.ORGANIZE_DESKTOP}:
                return tool_res

        # 5. General AI Chat / Question
        if self.settings.privacy_mode and not self.local_ai.available():
            return ToolResult(True, "Private Mode is enabled. External cloud AI routing is blocked.")

        try:
            ai_reply = self.ai.query(q)
            return ToolResult(True, ai_reply)
        except Exception as exc:
            return ToolResult(False, f"Unable to process query: {exc}")
