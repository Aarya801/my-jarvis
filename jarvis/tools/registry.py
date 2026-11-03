from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional
from jarvis.core.models import ToolResult, Risk
from jarvis.security.policy import PermissionManager
from jarvis.memory.store import MemoryStore

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    risk: Risk
    execute: Callable[..., ToolResult]

class ToolRegistry:
    """Central registry and executor for allowlisted JARVIS tools."""

    def __init__(self, permissions: PermissionManager, memory: MemoryStore):
        self.tools: Dict[str, Tool] = {}
        self.permissions = permissions
        self.memory = memory

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        return self.tools.get(tool_name)

    def run(self, tool_name: str, approved: bool = False, **kwargs) -> ToolResult:
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(False, f"Unrecognized tool directive: '{tool_name}'")

        # Dynamic risk assessment: previewing desktop organization is LOW risk (read-only)
        effective_risk = tool.risk
        if tool_name == "organize_desktop" and kwargs.get("preview", True):
            effective_risk = Risk.LOW

        ok, msg = self.permissions.check(effective_risk, approved)
        if not ok:
            pending = {
                "tool_name": tool_name,
                "kwargs": kwargs,
                "risk": effective_risk.value,
                "description": tool.description
            }
            return ToolResult(
                ok=False,
                message=msg,
                requires_confirmation=True,
                pending_action=pending
            )

        try:
            result = tool.execute(**kwargs)
        except Exception as exc:
            logging.exception(f"Execution error in tool '{tool_name}'")
            result = ToolResult(False, f"Tool '{tool_name}' failed safely: {exc}")

        # Audit log the execution
        try:
            self.memory.audit(
                tool=tool_name,
                action=str(kwargs),
                risk=effective_risk.value,
                approved=approved,
                result=result.message
            )
        except Exception:
            logging.warning("Failed to record audit log.")

        return result
