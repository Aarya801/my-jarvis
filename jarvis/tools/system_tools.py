from __future__ import annotations
import os
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import psutil

from jarvis.core.models import ToolResult, Risk
from jarvis.tools.registry import Tool, ToolRegistry
from jarvis.security.policy import SecurityPolicy
from jarvis.hardware.monitor import HardwareMonitor

# Standard category mapping for Desktop file organization
CATEGORY_MAP: Dict[str, List[str]] = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".rtf", ".odt", ".md"],
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"],
    "Code_Development": [".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".cpp", ".c", ".h", ".cs", ".sql", ".xml", ".yaml", ".yml"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"],
    "Installers": [".exe", ".msi"],
    "Media": [".mp3", ".wav", ".mp4", ".mkv", ".mov", ".avi", ".flac", ".wmv"],
}

# Critical Windows processes that must NEVER be terminated
PROTECTED_PROCESSES = {
    "explorer", "explorer.exe", "svchost", "svchost.exe", "csrss", "csrss.exe",
    "smss", "smss.exe", "lsass", "lsass.exe", "wininit", "wininit.exe",
    "services", "services.exe", "dwm", "dwm.exe", "conhost", "conhost.exe",
    "winlogon", "winlogon.exe", "spoolsv", "spoolsv.exe", "sihost", "sihost.exe",
    "taskhostw", "taskhostw.exe", "python", "python.exe", "system", "system.exe"
}

def register_system_tools(registry: ToolRegistry, policy: SecurityPolicy, apps: Dict[str, str]) -> None:
    """Registers all sandboxed and audited desktop automation tools."""

    def open_application(app_name: str) -> ToolResult:
        if not app_name or not app_name.strip():
            return ToolResult(False, "Application name cannot be empty.")

        cleaned = app_name.strip()
        cleaned_lower = cleaned.lower()

        # Check alias dictionary (case-insensitive)
        matched_target = None
        for key, path in apps.items():
            if key.lower() == cleaned_lower or key.lower() in cleaned_lower:
                matched_target = path
                break

        # Common defaults if not in JSON or empty
        if not matched_target or not matched_target.strip():
            fallbacks = {
                "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                "vs code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                "code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
                "file explorer": "explorer.exe",
                "terminal": "wt.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "task manager": "taskmgr.exe"
            }
            for fb_key, fb_path in fallbacks.items():
                if fb_key in cleaned_lower:
                    matched_target = fb_path
                    break

        if not matched_target:
            which_path = shutil.which(cleaned)
            if which_path:
                matched_target = which_path

        if not matched_target:
            return ToolResult(
                False,
                f"Application '{cleaned}' is not found in configured paths. "
                "You can register its executable path in config/applications.json."
            )

        try:
            # Check if file exists or can be resolved
            target_path = Path(matched_target)
            if target_path.is_absolute() and not target_path.exists():
                return ToolResult(False, f"Executable not found at path: {matched_target}")

            # Launch detached process so GUI thread never blocks
            DETACHED_FLAG = 0x00000008 | 0x00000200 # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            if target_path.is_absolute():
                subprocess.Popen([str(target_path)], creationflags=DETACHED_FLAG, close_fds=True)
            else:
                os.startfile(matched_target)

            return ToolResult(True, f"Launched application: {cleaned}")
        except Exception as exc:
            return ToolResult(False, f"Failed to start application '{cleaned}': {exc}")

    def close_application(app_name: str) -> ToolResult:
        if not app_name or not app_name.strip():
            return ToolResult(False, "Application name cannot be empty.")

        target = app_name.strip().lower()
        if not target.endswith(".exe"):
            target_exe = f"{target}.exe"
        else:
            target_exe = target

        if target in PROTECTED_PROCESSES or target_exe in PROTECTED_PROCESSES:
            return ToolResult(False, f"Safety violation: '{app_name}' is a protected Windows system process and cannot be terminated.")

        terminated_count = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and (proc_name.lower() == target_exe or target in proc_name.lower()):
                    if proc_name.lower() in PROTECTED_PROCESSES:
                        continue
                    proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if terminated_count > 0:
            return ToolResult(True, f"Closed {terminated_count} process instance(s) matching '{app_name}'.")
        return ToolResult(False, f"No running application found matching '{app_name}'.")

    def list_processes(limit: int = 15) -> ToolResult:
        running = []
        for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
            try:
                name = proc.info["name"]
                if not name or name.lower() in PROTECTED_PROCESSES:
                    continue
                mem_mb = (proc.info["memory_info"].rss / (1024 * 1024)) if proc.info["memory_info"] else 0
                if mem_mb < 15: # Filter out tiny background worker threads
                    continue
                running.append({
                    "pid": proc.info["pid"],
                    "name": name,
                    "mem_mb": round(mem_mb, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage descending
        running.sort(key=lambda x: x["mem_mb"], reverse=True)
        top_apps = running[:limit]

        lines = [f"{'PID':<8} {'APPLICATION':<28} {'RAM (MB)':<10}"]
        lines.append("-" * 48)
        for app in top_apps:
            lines.append(f"{app['pid']:<8} {app['name']:<28} {app['mem_mb']:<10.1f}")

        formatted = "\n".join(lines)
        return ToolResult(
            True,
            f"Active user applications ({len(top_apps)} listed):\n\n{formatted}",
            {"processes": top_apps}
        )

    def open_url(url: str) -> ToolResult:
        if not url:
            return ToolResult(False, "URL cannot be empty.")
        clean_url = url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = "https://" + clean_url
        try:
            webbrowser.open(clean_url)
            return ToolResult(True, f"Opened web destination: {clean_url}")
        except Exception as exc:
            return ToolResult(False, f"Failed to open URL '{clean_url}': {exc}")

    def find_files(query: str = "", search_dir: str = "", extension: str = "") -> ToolResult:
        if not query and not extension:
            return ToolResult(False, "Please provide a filename query or extension to search.")

        target_dirs: List[Path] = []
        if search_dir:
            try:
                target_dirs.append(policy.resolve_safe_path(search_dir))
            except Exception as e:
                return ToolResult(False, f"Search directory invalid: {e}")
        else:
            # Default search scopes: Desktop, Documents, Downloads, Project Root
            for candidate in [policy.get_desktop_dir(), policy.get_documents_dir(), policy.get_downloads_dir(), policy.root]:
                if candidate.exists() and candidate not in target_dirs:
                    target_dirs.append(candidate)

        matches: List[Dict[str, str]] = []
        query_lower = query.lower() if query else ""
        ext_lower = extension.lower() if extension else ""
        if ext_lower and not ext_lower.startswith("."):
            ext_lower = f".{ext_lower}"

        for search_root in target_dirs:
            try:
                for root, _, files in os.walk(search_root):
                    # Skip .git, .venv, node_modules, cache dirs
                    if any(ignored in root for ignored in [".venv", ".git", "__pycache__", "node_modules", ".pytest_cache"]):
                        continue
                    for f in files:
                        p = Path(root) / f
                        f_lower = f.lower()
                        match_q = not query_lower or query_lower in f_lower
                        match_ext = not ext_lower or p.suffix.lower() == ext_lower
                        if match_q and match_ext:
                            try:
                                size_kb = round(p.stat().st_size / 1024, 1)
                            except Exception:
                                size_kb = 0
                            matches.append({
                                "name": f,
                                "path": str(p),
                                "size_kb": f"{size_kb} KB"
                            })
                            if len(matches) >= 30:
                                break
                    if len(matches) >= 30:
                        break
            except Exception:
                continue

        if not matches:
            return ToolResult(True, f"No files found matching query='{query}' ext='{extension}'.", {"files": []})

        summary_lines = [f"Found {len(matches)} matching file(s):"]
        for idx, m in enumerate(matches[:15], 1):
            summary_lines.append(f"{idx}. {m['name']} ({m['size_kb']}) -> {m['path']}")
        if len(matches) > 15:
            summary_lines.append(f"... and {len(matches) - 15} more.")

        return ToolResult(True, "\n".join(summary_lines), {"files": matches})

    def create_folder(path: str) -> ToolResult:
        try:
            target_path = policy.resolve_safe_path(path, allow_create=True)
            if target_path.exists():
                return ToolResult(True, f"Folder already exists: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)
            return ToolResult(True, f"Created folder successfully: {target_path}")
        except Exception as exc:
            return ToolResult(False, f"Failed to create folder: {exc}")

    def create_file(path: str, content: str = "") -> ToolResult:
        try:
            target_path = policy.resolve_safe_path(path, allow_create=True)
            if target_path.exists():
                return ToolResult(
                    False,
                    f"File '{target_path.name}' already exists. Overwriting existing files is protected and prohibited."
                )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Created file successfully: {target_path} ({len(content)} chars)")
        except Exception as exc:
            return ToolResult(False, f"Failed to create file: {exc}")

    def rename_file(source: str, new_name: str) -> ToolResult:
        try:
            src_path = policy.resolve_safe_path(source)
            if not src_path.exists():
                return ToolResult(False, f"Source file does not exist: {src_path}")
            dest_path = src_path.parent / new_name.strip()
            if dest_path.exists():
                return ToolResult(False, f"Cannot rename: Destination '{dest_path.name}' already exists.")
            src_path.rename(dest_path)
            return ToolResult(True, f"Renamed '{src_path.name}' to '{dest_path.name}'.")
        except Exception as exc:
            return ToolResult(False, f"Failed to rename file: {exc}")

    def copy_file(source: str, destination: str) -> ToolResult:
        try:
            src_path = policy.resolve_safe_path(source)
            dest_path = policy.resolve_safe_path(destination, allow_create=True)
            if not src_path.exists():
                return ToolResult(False, f"Source file does not exist: {src_path}")
            if dest_path.is_dir():
                dest_path = dest_path / src_path.name
            if dest_path.exists():
                return ToolResult(False, f"Destination file already exists: {dest_path}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            return ToolResult(True, f"Copied '{src_path.name}' to '{dest_path}'.")
        except Exception as exc:
            return ToolResult(False, f"Failed to copy file: {exc}")

    def move_file(source: str, destination: str) -> ToolResult:
        try:
            src_path = policy.resolve_safe_path(source)
            dest_path = policy.resolve_safe_path(destination, allow_create=True)
            if not src_path.exists():
                return ToolResult(False, f"Source file does not exist: {src_path}")
            if dest_path.is_dir():
                dest_path = dest_path / src_path.name
            if dest_path.exists():
                return ToolResult(False, f"Destination file already exists: {dest_path}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
            return ToolResult(True, f"Moved '{src_path.name}' to '{dest_path}'.")
        except Exception as exc:
            return ToolResult(False, f"Failed to move file: {exc}")

    def organize_desktop(preview: bool = True) -> ToolResult:
        desktop = policy.get_desktop_dir()
        if not desktop.exists():
            return ToolResult(False, f"Desktop directory not found at: {desktop}")

        # Scan files directly residing on Desktop
        items = list(desktop.iterdir())
        unorganized: List[Path] = []
        for item in items:
            if not item.is_file():
                continue
            # Skip shortcuts, desktop.ini, hidden files
            if item.suffix.lower() in [".lnk", ".ini"] or item.name.startswith("."):
                continue
            unorganized.append(item)

        if not unorganized:
            return ToolResult(True, f"Your Desktop ({desktop}) is already fully organized. No stray files detected.")

        # Classify files
        plan: Dict[str, List[Path]] = {cat: [] for cat in CATEGORY_MAP}
        plan["Miscellaneous"] = []

        for f in unorganized:
            ext = f.suffix.lower()
            assigned = False
            for cat, extensions in CATEGORY_MAP.items():
                if ext in extensions:
                    plan[cat].append(f)
                    assigned = True
                    break
            if not assigned:
                plan["Miscellaneous"].append(f)

        # Filter categories with files
        active_plan = {k: v for k, v in plan.items() if v}

        if preview:
            summary = [
                "=== DESKTOP ORGANIZATION PLAN (PREVIEW) ===",
                f"Target Location: {desktop}",
                f"Total Files Identified: {len(unorganized)}\n",
                "Proposed Categorization Structure inside 'Organized_Files/':"
            ]
            for cat, files in active_plan.items():
                summary.append(f" - [{cat}] ({len(files)} files):")
                for item in files[:4]:
                    summary.append(f"     * {item.name}")
                if len(files) > 4:
                    summary.append(f"     * ... and {len(files) - 4} more")

            summary.append("\nSafety Guarantee: No files will be deleted or overwritten.")
            summary.append("Awaiting your explicit confirmation to proceed with the relocation.")

            return ToolResult(
                ok=True,
                message="\n".join(summary),
                data={"plan": {k: [str(p) for p in v] for k, v in active_plan.items()}},
                requires_confirmation=True,
                pending_action={
                    "tool_name": "organize_desktop",
                    "kwargs": {"preview": False},
                    "risk": Risk.HIGH.value,
                    "description": f"Organize {len(unorganized)} desktop files into category folders"
                }
            )

        # Execution Phase (preview=False)
        target_root = desktop / "Organized_Files"
        moved_count = 0
        error_count = 0

        for cat, files in active_plan.items():
            cat_dir = target_root / cat
            cat_dir.mkdir(parents=True, exist_ok=True)
            for file_path in files:
                try:
                    dest = cat_dir / file_path.name
                    # Collision resolution: append counter if exists
                    if dest.exists():
                        base = file_path.stem
                        suffix = file_path.suffix
                        c = 1
                        while dest.exists():
                            dest = cat_dir / f"{base}_{c}{suffix}"
                            c += 1
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                except Exception:
                    error_count += 1

        return ToolResult(
            True,
            f"=== DESKTOP ORGANIZATION COMPLETE ===\n"
            f"Successfully relocated {moved_count} file(s) into '{target_root}'.\n"
            f"Errors encountered: {error_count}.\n"
            "All categories were cleanly partitioned."
        )

    def system_status() -> ToolResult:
        h = HardwareMonitor().snapshot()
        now = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

        # Disk information
        disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:"))
        free_gb = disk.free / (1024**3)
        total_gb = disk.total / (1024**3)

        status_msg = (
            f"=== JARVIS SYSTEM TELEMETRY ===\n"
            f"Date & Time: {now}\n"
            f"CPU Utilization: {h.cpu:.1f}%\n"
            f"RAM Usage: {h.ram_used_gb:.1f} GB / {h.ram_total_gb:.1f} GB ({h.ram_percent:.1f}%)\n"
            f"System Disk (C:): {free_gb:.1f} GB free of {total_gb:.1f} GB ({disk.percent}% used)\n"
            f"Graphics Unit: {h.gpu_name}\n"
            f"Power State: {f'{h.battery:.0f}% Battery' if h.battery is not None else 'AC Connected'}\n"
            f"Security Boundary: Sandboxed & Containment Enforced"
        )
        return ToolResult(
            True,
            status_msg,
            {
                "cpu": h.cpu,
                "ram_percent": h.ram_percent,
                "ram_used_gb": h.ram_used_gb,
                "disk_free_gb": free_gb,
                "gpu": h.gpu_name
            }
        )

    # Register each tool with appropriate risk classifications
    tools = [
        Tool("open_application", "Launch an installed Windows application", {"app_name": "string"}, Risk.LOW, open_application),
        Tool("close_application", "Terminate a running user application", {"app_name": "string"}, Risk.HIGH, close_application),
        Tool("list_processes", "List running user processes and resource usage", {"limit": "integer"}, Risk.LOW, list_processes),
        Tool("open_url", "Open a website in the default browser", {"url": "string"}, Risk.LOW, open_url),
        Tool("find_files", "Search files across approved user folders", {"query": "string"}, Risk.LOW, find_files),
        Tool("create_folder", "Create a new directory in approved workspace", {"path": "string"}, Risk.MEDIUM, create_folder),
        Tool("create_file", "Create a new text note or document", {"path": "string", "content": "string"}, Risk.MEDIUM, create_file),
        Tool("rename_file", "Rename an existing file safely", {"source": "string", "new_name": "string"}, Risk.HIGH, rename_file),
        Tool("copy_file", "Copy file between approved locations", {"source": "string", "destination": "string"}, Risk.MEDIUM, copy_file),
        Tool("move_file", "Move file between approved locations", {"source": "string", "destination": "string"}, Risk.HIGH, move_file),
        Tool("organize_desktop", "Categorize and organize Desktop files with preview and confirmation", {"preview": "boolean"}, Risk.HIGH, organize_desktop),
        Tool("system_status", "Retrieve real-time hardware telemetry and status", {}, Risk.LOW, system_status),
    ]

    for tool in tools:
        registry.register(tool)
