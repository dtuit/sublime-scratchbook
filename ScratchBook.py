"""
ScratchBook - Sublime Text Plugin
==================================
Automatically saves untitled/scratch buffers to a scratchbook folder
and keeps your workspace clean.

INSTALLATION:
1. Copy this file to your Sublime Text Packages/User/ folder:
   - macOS:  ~/Library/Application Support/Sublime Text/Packages/User/
   - Linux:  ~/.config/sublime-text/Packages/User/
   - Windows: %APPDATA%/Sublime Text/Packages/User/

2. Copy the settings file (ScratchBook.sublime-settings) to the same folder.

3. (Optional) Add the recommended keybindings and settings below.

FEATURES:
- Auto-saves untitled buffers to ~/scratchbook/ on close or focus loss
- Timestamps filenames for easy identification
- Detects content type (JSON, XML, CSV, log, etc.) and uses appropriate extension
- "New Scratch Buffer" command that pre-configures a buffer for scratch use
- "Close All Scratch Tabs" command to bulk-close saved scratch buffers
- Configurable via settings file
"""

import sublime
import sublime_plugin
import os
import re
import json
import datetime


def get_settings():
    """Load plugin settings with defaults."""
    settings = sublime.load_settings("ScratchBook.sublime-settings")
    raw_folder = settings.get("scratchbook_folder", "")
    if not raw_folder:
        raw_folder = os.path.join(os.path.expanduser("~"), "scratchbook")
    else:
        # Expand ~ and environment variables (e.g. %USERPROFILE% on Windows)
        raw_folder = os.path.expandvars(os.path.expanduser(raw_folder))
        # If still relative, place it under user home
        if not os.path.isabs(raw_folder):
            raw_folder = os.path.join(os.path.expanduser("~"), raw_folder)
    return {
        "scratchbook_folder": raw_folder,
        "auto_save_on_close": settings.get("auto_save_on_close", True),
        "auto_save_on_focus_lost": settings.get("auto_save_on_focus_lost", True),
        "close_after_save": settings.get("close_after_save", False),
        "auto_detect_extension": settings.get("auto_detect_extension", True),
        "default_extension": settings.get("default_extension", ".txt"),
        "filename_format": settings.get("filename_format", "scratch_%Y%m%d_%H%M%S"),
        "min_content_length": settings.get("min_content_length", 1),
        "organize_by_date": settings.get("organize_by_date", False),
    }


def ensure_folder(path):
    """Create the scratchbook folder if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path


def detect_extension(content):
    """Detect file type from content and return appropriate extension."""
    content_stripped = content.strip()
    if not content_stripped:
        return ".txt"

    # JSON
    if (content_stripped.startswith("{") and content_stripped.endswith("}")) or (
        content_stripped.startswith("[") and content_stripped.endswith("]")
    ):
        try:
            json.loads(content_stripped)
            return ".json"
        except (json.JSONDecodeError, ValueError):
            pass

    # XML / HTML
    if content_stripped.startswith("<?xml") or re.match(
        r"^<[a-zA-Z][\s\S]*>[\s\S]*</[a-zA-Z]", content_stripped
    ):
        return ".xml"
    if re.match(r"(?i)^<!doctype html|^<html", content_stripped):
        return ".html"

    # CSV (heuristic: multiple lines with consistent comma/tab counts)
    lines = content_stripped.split("\n")[:10]
    if len(lines) >= 2:
        comma_counts = [line.count(",") for line in lines if line.strip()]
        tab_counts = [line.count("\t") for line in lines if line.strip()]
        if comma_counts and all(c == comma_counts[0] and c >= 2 for c in comma_counts):
            return ".csv"
        if tab_counts and all(c == tab_counts[0] and c >= 2 for c in tab_counts):
            return ".tsv"

    # Log files (lines starting with timestamps or log levels)
    log_pattern = re.compile(
        r"^(\d{4}[-/]\d{2}[-/]\d{2}|"
        r"\d{2}:\d{2}:\d{2}|"
        r"(DEBUG|INFO|WARN|ERROR|FATAL|TRACE)[\s:\|])",
        re.MULTILINE,
    )
    log_matches = log_pattern.findall(content_stripped)
    if len(log_matches) >= 3:
        return ".log"

    # SQL
    sql_keywords = re.compile(
        r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    if sql_keywords.search(content_stripped):
        return ".sql"

    # YAML
    if re.match(r"^---\s*$", content_stripped, re.MULTILINE) or re.match(
        r"^[a-zA-Z_][\w]*:\s", content_stripped
    ):
        return ".yaml"

    # Markdown
    if re.match(r"^#{1,6}\s", content_stripped) or re.search(
        r"\n#{1,6}\s", content_stripped
    ):
        return ".md"

    # Python
    if re.match(
        r"^(import |from |def |class |#!.*python)", content_stripped, re.MULTILINE
    ):
        return ".py"

    # JavaScript / TypeScript
    if re.match(
        r"^(const |let |var |function |import |export )", content_stripped, re.MULTILINE
    ):
        return ".js"

    return ".txt"


def generate_filename(content, settings):
    """Generate a unique filename for the scratch buffer."""
    now = datetime.datetime.now()
    base_name = now.strftime(settings["filename_format"])

    if settings["auto_detect_extension"]:
        ext = detect_extension(content)
    else:
        ext = settings["default_extension"]

    folder = settings["scratchbook_folder"]
    if settings["organize_by_date"]:
        folder = os.path.join(folder, now.strftime("%Y/%m"))

    ensure_folder(folder)

    filename = base_name + ext
    filepath = os.path.join(folder, filename)

    # Ensure uniqueness
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base_name}_{counter}{ext}"
        filepath = os.path.join(folder, filename)
        counter += 1

    return filepath


def save_scratch_buffer(view, settings=None, force_new=False):
    """Save a scratch/untitled buffer to the scratchbook folder.
    
    On first save, creates a new file and retargets the view to it.
    On subsequent saves, updates the existing linked file.
    """
    if settings is None:
        settings = get_settings()

    content = view.substr(sublime.Region(0, view.size()))
    if len(content.strip()) < settings["min_content_length"]:
        return None

    # Check if this view is already linked to a scratchbook file
    existing_file = view.file_name()
    scratchbook_folder = os.path.normpath(settings["scratchbook_folder"])

    if existing_file and os.path.normpath(existing_file).startswith(scratchbook_folder):
        # Already linked — just update the file in place
        try:
            with open(existing_file, "w", encoding="utf-8") as f:
                f.write(content)
            sublime.status_message(f"ScratchBook: Updated {os.path.basename(existing_file)}")
            return existing_file
        except Exception as e:
            sublime.error_message(f"ScratchBook: Failed to save - {e}")
            return None

    # Skip non-scratch files (files saved elsewhere on disk)
    if existing_file:
        return None

    # First save — create a new scratchbook file and link the view to it
    filepath = generate_filename(content, settings)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        # Retarget the view to the new file so it stays linked
        view.retarget(filepath)
        # Mark as scratch so Sublime won't prompt to save — we've already saved it
        view.set_scratch(True)
        sublime.status_message(f"ScratchBook: Saved to {os.path.basename(filepath)}")
        return filepath
    except Exception as e:
        sublime.error_message(f"ScratchBook: Failed to save - {e}")
        return None


class ScratchBookListener(sublime_plugin.EventListener):
    """Listens for buffer close and focus-lost events to auto-save."""

    _pending_saves = {}  # view_id -> timeout handle

    def _is_scratchbook_file(self, view, settings=None):
        """Check if a view's file lives in the scratchbook folder."""
        if settings is None:
            settings = get_settings()
        file_name = view.file_name()
        if not file_name:
            return False
        scratchbook_folder = os.path.normpath(settings["scratchbook_folder"])
        return os.path.normpath(file_name).startswith(scratchbook_folder)

    def _save_scratchbook_file(self, view):
        """Save a scratchbook file's content directly to disk."""
        file_name = view.file_name()
        if not file_name:
            return
        try:
            content = view.substr(sublime.Region(0, view.size()))
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(content)
            # Clear the dirty flag by reloading — but only if view is still valid
            if view.is_valid():
                view.set_scratch(True)
        except Exception as e:
            sublime.status_message(f"ScratchBook: Failed to save - {e}")

    def on_pre_close(self, view):
        settings = get_settings()
        if settings["auto_save_on_close"]:
            if not view.file_name():
                # Untitled buffer — save to scratchbook
                save_scratch_buffer(view, settings)
            elif self._is_scratchbook_file(view, settings):
                # Scratchbook file — write directly to disk before close
                self._save_scratchbook_file(view)

    def on_deactivated(self, view):
        settings = get_settings()
        if settings["auto_save_on_focus_lost"]:
            if not view.file_name():
                save_scratch_buffer(view, settings)
            elif self._is_scratchbook_file(view, settings):
                self._save_scratchbook_file(view)

    def on_modified(self, view):
        """Auto-save scratchbook files after a short delay when edited."""
        if not self._is_scratchbook_file(view):
            return

        view_id = view.id()

        # Cancel any pending save for this view
        if view_id in self._pending_saves:
            pass  # Previous timeout will check if still needed

        # Debounce: save 1 second after last edit
        def do_save():
            if view.is_valid() and self._is_scratchbook_file(view):
                self._save_scratchbook_file(view)
            self._pending_saves.pop(view_id, None)

        self._pending_saves[view_id] = True
        sublime.set_timeout(do_save, 1000)


class ScratchBookSaveCommand(sublime_plugin.TextCommand):
    """Manually save the current buffer to scratchbook."""

    def run(self, edit):
        filepath = save_scratch_buffer(self.view)
        if filepath:
            sublime.status_message(f"ScratchBook: Saved to {filepath}")
        else:
            sublime.status_message("ScratchBook: Nothing to save")


class ScratchBookNewCommand(sublime_plugin.WindowCommand):
    """Open a new scratch buffer (untitled, ready for pasting)."""

    def run(self):
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name("Scratch")
        sublime.status_message("ScratchBook: New scratch buffer created")


class ScratchBookCloseAllCommand(sublime_plugin.WindowCommand):
    """Close all untitled/scratch buffers (saves them first)."""

    def run(self):
        settings = get_settings()
        scratchbook_folder = os.path.normpath(settings["scratchbook_folder"])
        closed = 0
        for view in list(self.window.views()):
            file_name = view.file_name()
            is_untitled = not file_name
            is_scratchbook = (
                file_name
                and os.path.normpath(file_name).startswith(scratchbook_folder)
            )
            if is_untitled or is_scratchbook:
                save_scratch_buffer(view, settings)
                view.set_scratch(True)  # Prevent "save?" dialog
                view.close()
                closed += 1
        sublime.status_message(f"ScratchBook: Closed {closed} scratch tab(s)")


class ScratchBookOpenFolderCommand(sublime_plugin.WindowCommand):
    """Add the scratchbook folder to the current window's sidebar."""

    def run(self):
        settings = get_settings()
        folder = settings["scratchbook_folder"]
        ensure_folder(folder)

        project_data = self.window.project_data()

        # No active project — use open_folder if available, otherwise set project data
        if not project_data:
            project_data = {"folders": []}

        folders = project_data.get("folders", [])

        # Check if already in sidebar
        for f in folders:
            if os.path.normpath(f.get("path", "")) == os.path.normpath(folder):
                sublime.status_message("ScratchBook: Already in sidebar")
                return

        folders.append({"path": folder, "name": "ScratchBook"})
        project_data["folders"] = folders
        self.window.set_project_data(project_data)

        # Ensure the sidebar is visible
        self.window.run_command("toggle_side_bar") if not self.window.is_sidebar_visible() else None
        sublime.status_message("ScratchBook: Added to sidebar")


class ScratchBookBrowseCommand(sublime_plugin.WindowCommand):
    """Browse past scratch files in a searchable quick panel."""

    def run(self):
        settings = get_settings()
        folder = settings["scratchbook_folder"]
        ensure_folder(folder)

        # Collect all files recursively (supports organize_by_date subfolders)
        self.files = []
        for root, dirs, filenames in os.walk(folder):
            for fname in filenames:
                filepath = os.path.join(root, fname)
                self.files.append(filepath)

        if not self.files:
            sublime.status_message("ScratchBook: No saved scratch files found")
            return

        # Sort by modification time, newest first
        self.files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

        # Build quick panel items: [filename, first line preview]
        panel_items = []
        for filepath in self.files:
            fname = os.path.basename(filepath)
            # Get relative age
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            age = self._relative_time(mtime)
            # Read first line for preview
            preview = self._get_preview(filepath)
            panel_items.append([fname, f"{age}  ·  {preview}"])

        self.window.show_quick_panel(
            panel_items,
            self._on_select,
            sublime.MONOSPACE_FONT,
            0,
            self._on_highlight,
        )

    def _on_select(self, index):
        if index >= 0:
            self.window.open_file(self.files[index])

    def _on_highlight(self, index):
        if index >= 0:
            self.window.open_file(self.files[index], sublime.TRANSIENT)

    def _get_preview(self, filepath, max_len=80):
        """Read the first non-empty line of a file for preview."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if len(line) > max_len:
                            return line[:max_len] + "…"
                        return line
        except Exception:
            pass
        return "(empty)"

    def _relative_time(self, dt):
        """Return a human-readable relative time string."""
        now = datetime.datetime.now()
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days}d ago"
        else:
            return dt.strftime("%Y-%m-%d")
