from pathlib import Path
from jarvis.security.policy import SecurityPolicy, PermissionManager
from jarvis.memory.store import MemoryStore
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.system_tools import register_system_tools

def setup_test_registry(tmp_path):
    store = MemoryStore(tmp_path / "test.db")
    policy = SecurityPolicy(root=tmp_path)
    pm = PermissionManager(policy)
    reg = ToolRegistry(pm, store)
    apps = {"notepad": "notepad.exe", "calc": "calc.exe"}
    register_system_tools(reg, policy, apps)
    return reg, policy

def test_create_folder_and_file(tmp_path):
    reg, policy = setup_test_registry(tmp_path)

    # 1. Create folder
    target_dir = str(tmp_path / "SubFolder")
    res_folder = reg.run("create_folder", approved=True, path=target_dir)
    assert res_folder.ok
    assert (tmp_path / "SubFolder").exists()

    # 2. Create file with content
    target_file = str(tmp_path / "SubFolder" / "note.txt")
    res_file = reg.run("create_file", approved=True, path=target_file, content="Sample note text")
    assert res_file.ok
    assert (tmp_path / "SubFolder" / "note.txt").read_text(encoding="utf-8") == "Sample note text"

    # 3. Protect against silent overwrite
    res_overwrite = reg.run("create_file", approved=True, path=target_file, content="New text")
    assert not res_overwrite.ok
    assert "already exists" in res_overwrite.message

def test_file_copy_and_rename(tmp_path):
    reg, policy = setup_test_registry(tmp_path)
    src_file = tmp_path / "orig.txt"
    src_file.write_text("Original content", encoding="utf-8")

    # Copy file
    dest_copy = tmp_path / "orig_copy.txt"
    res_copy = reg.run("copy_file", approved=True, source=str(src_file), destination=str(dest_copy))
    assert res_copy.ok
    assert dest_copy.exists()
    assert dest_copy.read_text(encoding="utf-8") == "Original content"

    # Rename file
    res_rename = reg.run("rename_file", approved=True, source=str(dest_copy), new_name="renamed.txt")
    assert res_rename.ok
    assert (tmp_path / "renamed.txt").exists()
    assert not dest_copy.exists()

def test_find_files_in_temp_dir(tmp_path):
    reg, policy = setup_test_registry(tmp_path)
    (tmp_path / "script.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "doc.pdf").write_text("binary dummy", encoding="utf-8")

    res = reg.run("find_files", search_dir=str(tmp_path), extension=".py")
    assert res.ok
    assert len(res.data["files"]) >= 1
    assert any("script.py" in f["name"] for f in res.data["files"])
