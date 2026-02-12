# ScratchBook - Setup Guide
# ==========================

## Installation

Copy these files to your Sublime Text **Packages/User/** folder:

- `ScratchBook.py`
- `ScratchBook.sublime-settings`
- `ScratchBook.sublime-commands`
- `Main.sublime-menu`

**Folder locations:**
- **macOS:** `~/Library/Application Support/Sublime Text/Packages/User/`
- **Linux:** `~/.config/sublime-text/Packages/User/`
- **Windows:** `%APPDATA%\Sublime Text\Packages\User\`

The plugin activates immediately — no restart needed.

---

## Commands

Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and search for:

| Command                        | What it does                                       |
|--------------------------------|----------------------------------------------------|
| `ScratchBook: New Scratch`     | Opens a new disposable scratch buffer               |
| `ScratchBook: Save`            | Manually save current untitled buffer to scratchbook |
| `ScratchBook: Close All`       | Save & close all untitled tabs at once               |
| `ScratchBook: Browse`          | Searchable list of past scratch files with preview   |
| `ScratchBook: Open Folder`     | Add scratchbook folder to current window's sidebar   |

---

## Recommended Keybindings

Add these to your **Preferences → Key Bindings** file:

```json
[
    { "keys": ["ctrl+alt+n"], "command": "scratch_book_new" },
    { "keys": ["ctrl+alt+s"], "command": "scratch_book_save" },
    { "keys": ["ctrl+alt+w"], "command": "scratch_book_close_all" },
    { "keys": ["ctrl+alt+b"], "command": "scratch_book_browse" }
]
```

---

## How It Works

1. You paste text into a new untitled tab (your normal workflow).
2. You do your search/replace/formatting work.
3. When you close the tab, the content is **automatically saved** to `~/scratchbook/` with a timestamped filename.
4. The plugin **detects the content type** — JSON blobs get `.json`, log files get `.log`, XML gets `.xml`, etc.
5. Your scratchbook folder becomes a searchable archive of everything you've worked on.

No more "Do you want to save?" dialogs. No more losing useful scratch work. No more 100 tabs.
