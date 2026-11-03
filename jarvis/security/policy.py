from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple, Optional
from jarvis.core.models import Risk

class SecurityPolicy:
    """Security governance and boundary containment for JARVIS desktop operations."""

    def __init__(self, root: Optional[Path] = None, private_mode: bool = False):
        self.root = (root or Path(__file__).resolve().parents[2]).resolve()
        self.private_mode = private_mode
        self.user_home = Path.home().resolve()

        # Approved user locations where file and directory manipulation is permitted
        self.approved_directories: List[Path] = [
            self.root,
            self.user_home / "Desktop",
            self.user_home / "OneDrive" / "Desktop",
            self.user_home / "Documents",
            self.user_home / "OneDrive" / "Documents",
            self.user_home / "Downloads",
            self.user_home / "Pictures",
            self.user_home / "Music",
            self.user_home / "Videos",
        ]

        # System locations strictly forbidden from modification or deletion
        self.forbidden_prefixes: List[Path] = [
            Path(os.environ.get("SystemRoot", r"C:\Windows")).resolve(),
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")).resolve(),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).resolve(),
            Path(os.environ.get("ProgramData", r"C:\ProgramData")).resolve(),
        ]

    def requires_confirmation(self, risk: Risk) -> bool:
        """Determines if the given operational risk requires explicit user approval."""
        return risk in {Risk.MEDIUM, Risk.HIGH}

    def allows_network(self) -> bool:
        """Returns True if network operations (AI APIs, web research) are allowed."""
        return not self.private_mode

    def resolve_safe_path(self, path_str: str, allow_create: bool = False) -> Path:
        """
        Validates and resolves a path string, strictly preventing directory traversal
        and ensuring access remains inside approved user workspaces.
        """
        if not path_str or not path_str.strip():
            raise ValueError("Path argument cannot be empty.")

        raw_path = Path(path_str.strip()).expanduser()

        # If relative, resolve relative to user Desktop by default or project root
        if not raw_path.is_absolute():
            # Check if user Desktop exists
            desktop_dir = self.get_desktop_dir()
            target_path = (desktop_dir / raw_path).resolve()
        else:
            target_path = raw_path.resolve()

        # Check for traversal outside allowed trees
        is_approved = any(
            self._is_subpath(target_path, approved_dir.resolve())
            for approved_dir in self.approved_directories
            if approved_dir.exists()
        )

        # Also allow general subpaths of user home, provided they are not hidden sensitive dirs
        if not is_approved and self._is_subpath(target_path, self.user_home):
            sensitive_tokens = {".ssh", ".aws", ".azure", ".config", "AppData", "NTUSER.DAT"}
            target_parts = set(target_path.parts)
            if not sensitive_tokens.intersection(target_parts):
                is_approved = True

        # Check forbidden system locations
        for forbidden in self.forbidden_prefixes:
            if self._is_subpath(target_path, forbidden):
                raise PermissionError(f"Access denied: Path '{target_path}' lies within protected system directory '{forbidden}'.")

        if not is_approved:
            raise PermissionError(f"Access denied: Path '{target_path}' is outside approved user workspaces.")

        return target_path

    def get_desktop_dir(self) -> Path:
        """Detects whether standard Desktop or OneDrive Desktop is active."""
        onedrive_desktop = self.user_home / "OneDrive" / "Desktop"
        if onedrive_desktop.exists() and onedrive_desktop.is_dir():
            return onedrive_desktop
        standard_desktop = self.user_home / "Desktop"
        if standard_desktop.exists():
            return standard_desktop
        return self.user_home

    def get_downloads_dir(self) -> Path:
        downloads = self.user_home / "Downloads"
        return downloads if downloads.exists() else self.user_home

    def get_documents_dir(self) -> Path:
        onedrive_docs = self.user_home / "OneDrive" / "Documents"
        if onedrive_docs.exists():
            return onedrive_docs
        docs = self.user_home / "Documents"
        return docs if docs.exists() else self.user_home

    @staticmethod
    def _is_subpath(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

class PermissionManager:
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def check(self, risk: Risk, approved: bool = False) -> Tuple[bool, str]:
        if approved:
            return True, "Operation explicitly approved by user."
        if not self.policy.requires_confirmation(risk):
            return True, "Standard low-risk operation permitted."
        return False, f"Confirmation required: This {risk.value.upper()}-risk action requires your explicit approval."
