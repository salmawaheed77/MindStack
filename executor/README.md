# Sound OS — Command Execution Module

A modular Python command executor for Ubuntu/Linux. It accepts one JSON object per command and returns a JSON result.

## 1. Safety boundaries

- No arbitrary shell command execution is supported.
- Application launch/close is restricted to the allowlist in `command_executor/app_manager.py`.
- File operations are restricted to `~/SoundOS_Workspace`.
- File/folder deletion, logout, restart and shutdown require `confirmed: true`.
- Add new applications and actions deliberately; do not remove these checks.

## 2. Setup

```bash
sudo apt update
sudo apt install python3 python3-pip procps util-linux network-manager
mkdir -p ~/SoundOS_Workspace
```

Optional utilities for device controls:

```bash
sudo apt install brightnessctl
```

Audio controls use `wpctl` (PipeWire) or `pactl` (PulseAudio). They may already be installed.

## 3. Run

From this project folder:

```bash
python3 main.py
```

Enter one JSON command per line. Example:

```json
{"action":"get_disk_usage"}
{"action":"open_application","target":"firefox"}
{"action":"create_folder","path":"College"}
{"action":"create_file","path":"College/notes.txt","content":"My notes"}
{"action":"read_file","path":"College/notes.txt"}
{"action":"open_website","url":"https://www.youtube.com"}
{"action":"volume_up"}
{"action":"lock_screen"}
```

To delete a file, the application must first obtain explicit user approval and then send:

```json
{"action":"delete_file","path":"College/notes.txt","confirmed":true}
```

The same confirmation rule applies to deleting folders, logout, restart and shutdown.

## 4. Supported actions

### Applications
- `open_application`, `close_application`, `list_running_applications`
- Initial allowlist: `calculator`, `firefox`, `files`, `text_editor`, `gedit`, `terminal`, `vlc`, `libreoffice`, `code`
- Edit `APPS` in `command_executor/app_manager.py` to add applications installed on your Ubuntu system.

### Files and folders
- `create_folder` with `path`
- `create_file` with `path`, optional `content`
- `read_file` with `path`
- `copy_file` with `source`, `destination`
- `move_file` with `source`, `destination`
- `rename_file` with `path`, `new_name`
- `delete_file` with `path`, `confirmed: true`
- `delete_folder` with `path`, `confirmed: true`
- `search_files` with `query`, optional `folder`
- `list_files` with optional `folder`

Paths are relative to `~/SoundOS_Workspace`, e.g. `College/notes.txt`.

### Browser
- `open_website` with `url` (http/https only)
- `google_search` with `query`

### System
- `get_date_time`, `get_disk_usage`, `get_memory_usage`, `get_system_info`
- `lock_screen`
- `logout`, `restart_system`, `shutdown_system` (confirmation required)

### Devices
- `volume_up`, `volume_down`, `volume_mute`
- `brightness_up`, `brightness_down` (requires `brightnessctl` and hardware support)
- `wifi_on`, `wifi_off` (requires NetworkManager / `nmcli`)

## 5. Test

```bash
python3 -m unittest discover -s tests -v
```

## 6. Integration contract with the AI teammate

The AI module should send a dictionary with:
- `action`: one supported action string
- additional fields required by that action, such as `target`, `path`, `url` or `query`
- `confirmed: true` only after the user explicitly approves a destructive or power action

Call from another Python module:

```python
from command_executor.executor import execute_command

result = execute_command({
    "action": "get_disk_usage"
})
print(result)
```

This module is an execution layer, not speech recognition or natural-language understanding. The speech/AI modules should convert the user's request into this structured format.
