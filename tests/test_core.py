from pathlib import Path
import json
from jarvis.core.config import load_settings
from jarvis.core.models import Risk, ToolResult
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.tools.registry import Tool, ToolRegistry

def test_settings_load():
    settings = load_settings()
    assert settings.local_model == "qwen2.5:3b"

def test_permissions_require_approval():
    policy = SecurityPolicy()
    pm = PermissionManager(policy)
    assert not pm.check(Risk.HIGH)[0]
    assert pm.check(Risk.HIGH, approved=True)[0]
    assert pm.check(Risk.LOW)[0]

def test_memory_round_trip(tmp_path):
    store = MemoryStore(tmp_path / "jarvis.db")
    store.remember("Python preference")
    memories = store.memories()
    assert len(memories) == 1
    assert memories[0][2] == "Python preference"

def test_registry_audits_and_calls(tmp_path):
    store = MemoryStore(tmp_path / "j.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    reg.register(Tool("ok_tool", "A test tool", {}, Risk.LOW, lambda: ToolResult(True, "done")))
    res = reg.run("ok_tool")
    assert res.ok
    assert res.message == "done"

def test_config_json(tmp_path):
    app_json = Path(__file__).parents[1] / "config" / "applications.json"
    with open(app_json, "r", encoding="utf-8-sig") as f:
        apps = json.load(f)
    assert "Chrome" in apps
    assert "Notepad" in apps
