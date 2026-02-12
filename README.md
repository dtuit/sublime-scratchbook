# ScratchBook

A Sublime Text plugin that automatically saves untitled buffers to `~/scratchbook/` when you close them.

## Features

- Auto-saves untitled buffers on close
- Detects content type (JSON, XML, HTML, CSV, SQL, YAML, Markdown, Python, JS, logs)
- Timestamped filenames (`scratch_20250212_143052.json`)
- Browse and search saved scratch files

## Installation

Copy these files to your Sublime Text **Packages/User/** folder:

```
ScratchBook.py
ScratchBook.sublime-settings
ScratchBook.sublime-commands
Main.sublime-menu
```

| Platform | Location |
|----------|----------|
| macOS | `~/Library/Application Support/Sublime Text/Packages/User/` |
| Linux | `~/.config/sublime-text/Packages/User/` |
| Windows | `%APPDATA%\Sublime Text\Packages\User\` |

No restart required.

## Commands

Available via Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`):

| Command | Description |
|---------|-------------|
| **ScratchBook: New Scratch** | Open a new scratch buffer |
| **ScratchBook: Save** | Manually save current buffer |
| **ScratchBook: Close All** | Save and close all scratch tabs |
| **ScratchBook: Browse** | Search saved scratch files |
| **ScratchBook: Open Folder** | Add scratchbook folder to sidebar |

## Keybindings

Add to **Preferences → Key Bindings**:

```json
[
    { "keys": ["ctrl+alt+n"], "command": "scratch_book_new" },
    { "keys": ["ctrl+alt+s"], "command": "scratch_book_save" },
    { "keys": ["ctrl+alt+w"], "command": "scratch_book_close_all" },
    { "keys": ["ctrl+alt+b"], "command": "scratch_book_browse" }
]
```

## Configuration

Edit `ScratchBook.sublime-settings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `scratchbook_folder` | `"scratchbook"` | Save location (relative to home or absolute path) |
| `auto_save_on_close` | `true` | Save when closing tabs |
| `auto_save_on_focus_lost` | `false` | Save when switching tabs |
| `auto_detect_extension` | `true` | Detect filetype from content |
| `default_extension` | `".txt"` | Fallback extension |
| `filename_format` | `"scratch_%Y%m%d_%H%M%S"` | Filename pattern (strftime) |
| `min_content_length` | `1` | Minimum characters to save |
| `organize_by_date` | `false` | Use YYYY/MM subfolders |

## License

MIT
