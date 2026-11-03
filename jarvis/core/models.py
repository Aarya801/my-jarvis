from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

class Risk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ToolResult:
    ok: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    pending_action: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "data": self.data,
            "requires_confirmation": self.requires_confirmation,
            "pending_action": self.pending_action
        }
