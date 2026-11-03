from jarvis.core.router import CommandRouter
from jarvis.core.nlu import NaturalLanguageParser
from jarvis.core.models import Risk, ToolResult
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.tools.registry import Tool, ToolRegistry
from jarvis.tools.system_tools import register_system_tools
from jarvis.ai.providers import LocalAIProvider, CloudAIProvider
from jarvis.core.config import load_settings

def test_router_end_to_end(tmp_path):
    settings = load_settings(tmp_path)
    store = MemoryStore(tmp_path / "test.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    register_system_tools(reg, policy, {"notepad": "notepad.exe"})

    class MockLocalAI:
        def available(self): return True
        def chat(self, p): return "Mock response to " + p

    class MockCloudAI:
        def available(self): return False
        def chat(self, p): return ""

    router = CommandRouter(
        registry=reg,
        memory=store,
        local_ai=MockLocalAI(),
        cloud_ai=MockCloudAI(),
        settings=settings
    )

    # 1. Greeting
    res_greet = router.handle("hello jarvis")
    assert res_greet.ok
    assert "J.A.R.V.I.S." in res_greet.message

    # 2. Status
    res_status = router.handle("How much RAM am I using?")
    assert res_status.ok
    assert "CPU" in res_status.message

    # 3. Protected process termination block
    res_close = router.handle("close explorer", approved=True)
    assert not res_close.ok
    assert "protected Windows system process" in res_close.message

    # 4. Confirmation re-play for high-risk action
    pending = {
        "tool_name": "create_folder",
        "kwargs": {"path": str(tmp_path / "ApprovedFolder")},
        "risk": "medium",
        "description": "Create folder"
    }
    res_approved = router.handle("", approved=True, pending_action=pending)
    assert res_approved.ok
    assert (tmp_path / "ApprovedFolder").exists()
