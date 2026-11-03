from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

class Intent(str, Enum):
    GREETING = "greeting"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    OPEN_URL = "open_url"
    LIST_PROCESSES = "list_processes"
    FIND_FILES = "find_files"
    CREATE_FOLDER = "create_folder"
    CREATE_FILE = "create_file"
    ORGANIZE_DESKTOP = "organize_desktop"
    SYSTEM_STATUS = "system_status"
    DATE_TIME = "date_time"
    REMINDER = "reminder"
    SCREEN_VISION = "screen_vision"
    AI_CHAT = "ai_chat"

@dataclass
class ParsedCommand:
    intent: Intent
    tool_name: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    raw_query: str = ""

class NaturalLanguageParser:
    """Robust natural language interpretation layer for desktop commands."""

    COMMON_SITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://www.github.com",
        "stackoverflow": "https://stackoverflow.com",
        "reddit": "https://www.reddit.com",
        "linkedin": "https://www.linkedin.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "wikipedia": "https://www.wikipedia.org",
        "chatgpt": "https://chat.openai.com",
    }

    FILE_EXT_ALIASES = [
        ("python files", ".py"), ("python file", ".py"), ("python", ".py"), ("py files", ".py"),
        ("pdf files", ".pdf"), ("pdfs", ".pdf"), ("pdf", ".pdf"),
        ("word documents", ".docx"), ("word files", ".docx"), ("word", ".docx"), ("docx", ".docx"),
        ("excel files", ".xlsx"), ("spreadsheets", ".xlsx"), ("xlsx", ".xlsx"), ("csv files", ".csv"), ("csv", ".csv"),
        ("text files", ".txt"), ("text file", ".txt"), ("txt files", ".txt"), ("notes", ".txt"),
        ("image files", ".png"), ("images", ".png"), ("photos", ".jpg"), ("pictures", ".jpg"),
        ("video files", ".mp4"), ("videos", ".mp4"), ("mp4", ".mp4"),
        ("music files", ".mp3"), ("audio files", ".mp3"), ("songs", ".mp3"), ("mp3", ".mp3"),
        ("zip files", ".zip"), ("archives", ".zip"), ("zip", ".zip")
    ]

    def parse(self, text: str) -> ParsedCommand:
        raw = text.strip()
        low = raw.lower()

        # 1. Greetings
        if low in {"hi", "hello", "hey", "hey jarvis", "jarvis", "hi jarvis", "hello jarvis", "wake up", "good morning", "good evening"} or any(low.startswith(g) for g in ["hello jarvis", "hey jarvis", "hi jarvis"]):
            return ParsedCommand(intent=Intent.GREETING, raw_query=raw)

        # 2. Screen awareness
        if any(p in low for p in ["look at my screen", "analyze my screen", "what is on my screen", "look at this page", "capture screen"]):
            return ParsedCommand(intent=Intent.SCREEN_VISION, raw_query=raw)

        # 3. Desktop organization
        if re.search(r"\b(organize|clean up|tidy|sort)\b.*\bdesktop\b", low) or low == "organize my desktop":
            return ParsedCommand(
                intent=Intent.ORGANIZE_DESKTOP,
                tool_name="organize_desktop",
                params={"preview": True},
                confidence=0.98,
                raw_query=raw
            )

        # 4. System telemetry & hardware status
        if any(p in low for p in ["how much ram", "ram am i using", "ram usage", "cpu usage", "system status", "battery status", "hardware status", "telemetry", "how much memory"]):
            return ParsedCommand(
                intent=Intent.SYSTEM_STATUS,
                tool_name="system_status",
                confidence=0.95,
                raw_query=raw
            )

        # 5. Date & Time
        if any(p in low for p in ["what time is it", "current time", "what is the date", "today's date", "time now", "tell me the time"]):
            return ParsedCommand(
                intent=Intent.DATE_TIME,
                tool_name="system_status",
                confidence=0.95,
                raw_query=raw
            )

        # 6. Running applications / processes
        if any(p in low for p in [
            "what applications are currently running", "what applications are running",
            "what apps are running", "list running apps", "show active processes",
            "running processes", "list processes", "what is running"
        ]):
            return ParsedCommand(
                intent=Intent.LIST_PROCESSES,
                tool_name="list_processes",
                params={"limit": 15},
                confidence=0.95,
                raw_query=raw
            )

        # 7. Close / Terminate application
        close_match = re.search(r"^(?:close|quit|kill|terminate|exit)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+application|\s+app)?$", low)
        if close_match:
            app_target = close_match.group(1).strip()
            return ParsedCommand(
                intent=Intent.CLOSE_APP,
                tool_name="close_application",
                params={"app_name": app_target},
                confidence=0.95,
                raw_query=raw
            )

        # 8. Web URLs and known sites
        if low.startswith("open "):
            target = raw[5:].strip()
            target_low = target.lower()

            # Check direct URL
            if re.match(r"^https?://", target_low):
                return ParsedCommand(
                    intent=Intent.OPEN_URL,
                    tool_name="open_url",
                    params={"url": target},
                    confidence=0.98,
                    raw_query=raw
                )

            # Check known website name
            if target_low in self.COMMON_SITES:
                return ParsedCommand(
                    intent=Intent.OPEN_URL,
                    tool_name="open_url",
                    params={"url": self.COMMON_SITES[target_low]},
                    confidence=0.98,
                    raw_query=raw
                )

            # Check website with TLD
            if re.match(r"^[a-zA-Z0-9\-]+\.(com|org|net|edu|io|ai|dev|co)$", target_low):
                return ParsedCommand(
                    intent=Intent.OPEN_URL,
                    tool_name="open_url",
                    params={"url": f"https://{target_low}"},
                    confidence=0.98,
                    raw_query=raw
                )

            # Check project folder (e.g. "open my ASTRA-66 project")
            proj_match = re.search(r"^(?:my\s+)?(.+?)\s+project$", target, re.IGNORECASE)
            if proj_match:
                proj_name = proj_match.group(1).strip()
                return ParsedCommand(
                    intent=Intent.FIND_FILES,
                    tool_name="find_files",
                    params={"query": proj_name},
                    confidence=0.9,
                    raw_query=raw
                )

            # Otherwise, application launch
            return ParsedCommand(
                intent=Intent.OPEN_APP,
                tool_name="open_application",
                params={"app_name": target},
                confidence=0.92,
                raw_query=raw
            )

        # Launch / start application
        launch_match = re.search(r"^(?:launch|start|run)\s+(.+)$", low)
        if launch_match:
            app_target = launch_match.group(1).strip()
            return ParsedCommand(
                intent=Intent.OPEN_APP,
                tool_name="open_application",
                params={"app_name": app_target},
                confidence=0.9,
                raw_query=raw
            )

        # 9. Folder creation: "Create a folder called College Projects on my desktop"
        folder_match = re.search(
            r"(?:create|make|new)\s+(?:a\s+)?folder\s+(?:called|named\s+)?['\"]?([^'\"\n]+?)['\"]?(?:\s+on\s+my\s+|\s+in\s+)?(desktop|documents|downloads)?$",
            low
        )
        if folder_match:
            folder_name = folder_match.group(1).strip()
            location = folder_match.group(2) or "desktop"
            target_path = f"{location.capitalize()}/{folder_name}"
            return ParsedCommand(
                intent=Intent.CREATE_FOLDER,
                tool_name="create_folder",
                params={"path": target_path},
                confidence=0.95,
                raw_query=raw
            )

        # 10. File creation / Notes:
        # e.g. "Make a new text file with today's study plan"
        # e.g. "create a text file called notes.txt with hello"
        file_pattern = re.search(
            r"(?:make|create|write)\s+(?:a\s+)?(?:new\s+)?(?:text\s+file|note|file)\s*(?:called|named)?\s*['\"]?([^'\"\n]*?)['\"]?\s*(?:with\s+(?:content|text)?:?\s*(.*))?$",
            raw,
            re.IGNORECASE
        )
        if file_pattern and ("file" in low or "note" in low):
            name_part = file_pattern.group(1).strip()
            content_part = file_pattern.group(2).strip() if file_pattern.group(2) else ""

            if not name_part and content_part:
                # e.g. "make a new text file with today's study plan"
                # content_part = "today's study plan" -> file_name = "today_study_plan.txt"
                name_clean = re.sub(r"[^\w\s]", "", content_part).strip().replace(" ", "_")
                file_name = f"{name_clean[:30]}.txt"
                content = f"# Study Plan / Notes\n{content_part}\n"
            elif name_part:
                file_name = name_part if "." in name_part else f"{name_part.replace(' ', '_')}.txt"
                content = content_part or f"# {name_part}\nCreated by JARVIS.\n"
            else:
                file_name = "new_note.txt"
                content = "# Note\nCreated by JARVIS.\n"

            return ParsedCommand(
                intent=Intent.CREATE_FILE,
                tool_name="create_file",
                params={"path": f"Desktop/{file_name}", "content": content},
                confidence=0.94,
                raw_query=raw
            )

        # 11. File searching: "Find my Python files", "Search my Downloads folder for PDFs"
        search_match = re.search(r"^(?:find|search(?:\s+for)?)\s+(.+)$", low)
        if search_match:
            query_body = search_match.group(1).strip()

            # Detect location
            search_dir = ""
            for loc in ["downloads", "documents", "desktop"]:
                loc_pattern = rf"\b(?:in|on|my)\s+{loc}\b"
                if re.search(loc_pattern, query_body):
                    search_dir = loc.capitalize()
                    query_body = re.sub(loc_pattern, "", query_body).strip()
                    break

            # Detect extension using alias list
            extension = ""
            for alias, ext in self.FILE_EXT_ALIASES:
                alias_pattern = rf"\b{re.escape(alias)}\b"
                if re.search(alias_pattern, query_body):
                    extension = ext
                    query_body = re.sub(alias_pattern, "", query_body).strip()
                    break

            # Clean residual words
            clean_query = re.sub(r"\b(my|files|folder|for|all)\b", "", query_body).strip()

            return ParsedCommand(
                intent=Intent.FIND_FILES,
                tool_name="find_files",
                params={"query": clean_query, "search_dir": search_dir, "extension": extension},
                confidence=0.94,
                raw_query=raw
            )

        # 12. Reminders: "remind me to study algorithms at 8pm"
        if low.startswith("remind me "):
            content = raw[10:].strip()
            return ParsedCommand(
                intent=Intent.REMINDER,
                params={"content": content},
                confidence=0.9,
                raw_query=raw
            )

        # 13. General AI Chat / Question
        return ParsedCommand(
            intent=Intent.AI_CHAT,
            params={"prompt": raw},
            confidence=0.85,
            raw_query=raw
        )
