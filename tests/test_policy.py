import pytest
from pathlib import Path
from jarvis.security.policy import SecurityPolicy
from jarvis.core.models import Risk

def test_policy_allows_safe_user_paths(tmp_path):
    policy = SecurityPolicy(root=tmp_path)
    safe_path = policy.resolve_safe_path(str(tmp_path / "my_project_file.txt"))
    assert safe_path == (tmp_path / "my_project_file.txt").resolve()

def test_policy_blocks_system_directory_traversal(tmp_path):
    policy = SecurityPolicy(root=tmp_path)
    with pytest.raises(PermissionError):
        policy.resolve_safe_path(r"C:\Windows\System32\cmd.exe")

def test_policy_blocks_program_files(tmp_path):
    policy = SecurityPolicy(root=tmp_path)
    with pytest.raises(PermissionError):
        policy.resolve_safe_path(r"C:\Program Files\Common Files\something.dll")

def test_policy_confirmation_rules():
    policy = SecurityPolicy()
    assert policy.requires_confirmation(Risk.HIGH)
    assert policy.requires_confirmation(Risk.MEDIUM)
    assert not policy.requires_confirmation(Risk.LOW)
