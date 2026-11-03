from pathlib import Path
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.system_tools import register_system_tools

def test_desktop_organizer_flow(tmp_path):
    mock_desktop = tmp_path / "Desktop"
    mock_desktop.mkdir()

    # Create test files
    (mock_desktop / "doc.pdf").write_text("dummy pdf", encoding="utf-8")
    (mock_desktop / "photo.png").write_text("dummy img", encoding="utf-8")
    (mock_desktop / "script.py").write_text("dummy code", encoding="utf-8")
    (mock_desktop / "archive.zip").write_text("dummy zip", encoding="utf-8")
    (mock_desktop / "app.exe").write_text("dummy exe", encoding="utf-8")
    (mock_desktop / "notes.txt").write_text("dummy txt", encoding="utf-8")

    # Policy pointing to mock desktop
    policy = SecurityPolicy(root=tmp_path)
    policy.get_desktop_dir = lambda: mock_desktop
    pm = PermissionManager(policy)
    store = MemoryStore(tmp_path / "mem.db")
    reg = ToolRegistry(pm, store)
    register_system_tools(reg, policy, {})

    # 1. Preview phase (requires confirmation, moves nothing)
    preview_res = reg.run("organize_desktop", preview=True)
    assert preview_res.ok
    assert preview_res.requires_confirmation
    assert preview_res.pending_action is not None
    assert "PLAN (PREVIEW)" in preview_res.message
    assert (mock_desktop / "doc.pdf").exists()

    # 2. Execution phase (approved=True, preview=False)
    exec_res = reg.run("organize_desktop", approved=True, preview=False)
    assert exec_res.ok
    assert "ORGANIZATION COMPLETE" in exec_res.message

    # Verify organized folder structure
    org_root = mock_desktop / "Organized_Files"
    assert org_root.exists()
    assert (org_root / "Documents" / "doc.pdf").exists()
    assert (org_root / "Documents" / "notes.txt").exists()
    assert (org_root / "Images" / "photo.png").exists()
    assert (org_root / "Code_Development" / "script.py").exists()
    assert (org_root / "Archives" / "archive.zip").exists()
    assert (org_root / "Installers" / "app.exe").exists()
