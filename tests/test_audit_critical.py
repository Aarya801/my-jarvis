import pytest
from pathlib import Path
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.system_tools import register_system_tools
from jarvis.ai.providers import CompositeAI, LocalAIProvider, CloudAIProvider
from jarvis.core.config import Settings
from jarvis.core.models import Risk

def test_ollama_unavailable_fallback(tmp_path):
    """Verify that when both Ollama and Cloud AI are unavailable, an informative offline message is returned."""
    settings = Settings(
        root=tmp_path,
        ai_mode="auto",
        local_provider="ollama",
        local_url="http://localhost:11434",
        local_model="qwen2.5:3b",
        cloud_provider="openai",
        cloud_api_key="",
        cloud_model="gpt-4o",
        privacy_mode=False,
        performance_mode="balanced",
        tts_enabled=False,
        stt_enabled=False,
        memory_enabled=False,
        vision_model="",
        voice_enabled=False
    )

    class MockOfflineLocal:
        def available(self): return False
        def chat(self, p): return ""

    class MockOfflineCloud:
        def available(self): return False
        def chat(self, p): return ""

    composite = CompositeAI(MockOfflineLocal(), MockOfflineCloud(), settings)
    reply = composite.query("What is the capital of France?")
    assert "offline mode" in reply.lower()
    assert "ollama" in reply.lower()

def test_denied_traversal_paths(tmp_path):
    """Verify that path traversal attempts to escape to system directories are strictly blocked."""
    policy = SecurityPolicy(root=tmp_path)

    # Path traversal attack
    traversal_str = str(tmp_path / ".." / ".." / "Windows" / "System32" / "cmd.exe")
    with pytest.raises(PermissionError):
        policy.resolve_safe_path(traversal_str)

    # Windows root directory
    with pytest.raises(PermissionError):
        policy.resolve_safe_path(r"C:\Windows\explorer.exe")

    # Program files
    with pytest.raises(PermissionError):
        policy.resolve_safe_path(r"C:\Program Files\Common Files")

def test_protected_system_processes(tmp_path):
    """Verify that protected Windows system processes cannot be terminated even when approved."""
    store = MemoryStore(tmp_path / "test.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    register_system_tools(reg, policy, {})

    for proc in ["explorer.exe", "svchost.exe", "dwm.exe", "system"]:
        res = reg.run("close_application", approved=True, app_name=proc)
        assert not res.ok
        assert "protected Windows system process" in res.message

def test_file_overwrite_protection(tmp_path):
    """Verify that create_file and copy_file never silently overwrite existing files."""
    store = MemoryStore(tmp_path / "test.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    register_system_tools(reg, policy, {})

    existing_file = tmp_path / "protected.txt"
    existing_file.write_text("Original safe content", encoding="utf-8")

    # Attempting to create same file
    res_create = reg.run("create_file", approved=True, path=str(existing_file), content="Malicious overwrite")
    assert not res_create.ok
    assert "already exists" in res_create.message
    assert existing_file.read_text(encoding="utf-8") == "Original safe content"

def test_operation_cancellation(tmp_path):
    """Verify that risky operations without approval return requires_confirmation=True and do not execute."""
    store = MemoryStore(tmp_path / "test.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    register_system_tools(reg, policy, {})

    dest_dir = tmp_path / "UnapprovedFolder"
    # Unapproved call
    res = reg.run("create_folder", approved=False, path=str(dest_dir))
    assert not res.ok
    assert res.requires_confirmation
    assert not dest_dir.exists()
