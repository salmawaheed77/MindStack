# MindStack — Executor Module (updated)

This folder is the structured command-execution layer for MindStack. It does **not** contain STT, NLP, GUI code, or a general-purpose shell.

## What changed in this version

- Fixed package imports: use `executor.executor`, not the old/nonexistent `command_executor` package.
- Kept a single public entry point: `execute_command(payload)`.
- Added `get_cpu_usage` and `get_processes` actions to match the GUI command catalogue.
- Tightened workspace path checks and reject symbolic links in user-supplied paths.
- Prevented accidental overwrites in create, copy, move, and rename operations.
- Fixed nested-folder rename path handling.
- Made confirmation failures explicit with `error="confirmation_required"` and `confirmation_required=true`.
- Added clearer error codes and tests.
- Kept application launching allowlisted and all subprocess calls shell-free.

## Latest changes

- `get_processes` now returns the top 10 processes by memory use (`memory_percent`). Optional fields: `limit` (1-100) and `sort_by` (`memory` or `pid`).
- `text_editor` uses `gedit` if installed, otherwise `gnome-text-editor`. `gnome_text_editor` is also an allowed name.
- The workspace folder `~/MindStack_Workspace` is created with owner-only permissions (700).

- `terminal` and `code` are no longer allowed applications (they give a shell). Process names are compared with the kernel's 15-character limit, so `close_application` now works for `gnome-calculator` and `gnome-text-editor`.
- `folder: ""` or `null` in `list_files` / `search_files` means the workspace root.

- **Security fix:** approval can no longer be sent inside the payload; use `execute_command(action, confirmed=True)`.
- Error messages are short and speakable (no `[Errno ...]`, no full paths). `lock_screen`, `logout`, `restart_system` and `shutdown_system` now report failures instead of always saying "requested". Launched applications no longer print to the terminal. `list_running_applications` returns full process names. Each executed action is logged by the `mindstack.executor` logger.

## Requirements

- Python 3.10+
- Ubuntu/Linux for `/proc`-based CPU, memory, and process information
- Optional OS utilities depending on the action: `ps`, `pkill`, `loginctl`, `systemctl`, `nmcli`, `wpctl` or `pactl`, `brightnessctl`, and installed desktop applications.

Example Ubuntu packages:

```bash
sudo apt update
sudo apt install procps util-linux network-manager
# Optional brightness control:
sudo apt install brightnessctl
```

Audio controls use `wpctl` (PipeWire) or `pactl` (PulseAudio), if available.

## Workspace and file safety

All file operations are restricted to `~/MindStack_Workspace`. Relative paths are recommended:

```json
{"action":"create_folder","path":"College"}
{"action":"create_file","path":"College/notes.txt","content":"My notes"}
{"action":"read_file","path":"College/notes.txt"}
```

The executor rejects paths that escape the workspace and rejects symbolic-link components. It does not overwrite an existing destination. Choose a new destination name instead.

Deleting files/folders and logging out, restarting, or shutting down require explicit approval from the user.

```python
result = execute_command({"action": "delete_file", "path": "College/notes.txt"})
# -> {"success": False, "error": "confirmation_required", "confirmation_required": True, ...}

# Only after the USER approved this exact action (dialog, spoken "yes", ...):
result = execute_command({"action": "delete_file", "path": "College/notes.txt"}, confirmed=True)
```

Approval is a separate argument (`confirmed=True`), **not** a field of the action. A `confirmed` field (or any key starting with `_`) inside the action dictionary is removed and ignored, so the NLP model cannot approve a dangerous action by itself. Never pass `confirmed=True` automatically or merely because a settings toggle disables confirmation dialogs.

## Supported actions

| Category | Actions |
|---|---|
| Applications | `open_application`, `close_application`, `list_running_applications` |
| Files | `create_folder`, `create_file`, `read_file`, `copy_file`, `move_file`, `rename_file`, `delete_file`, `delete_folder`, `search_files`, `list_files` |
| Browser | `open_website`, `google_search` |
| System | `get_date_time`, `get_cpu_usage`, `get_disk_usage`, `get_memory_usage`, `get_processes`, `get_system_info`, `lock_screen`, `logout`, `restart_system`, `shutdown_system` |
| Devices | `volume_up`, `volume_down`, `volume_mute`, `brightness_up`, `brightness_down`, `wifi_on`, `wifi_off` |

Application names are allowlisted in `app_manager.py`. `browser` is an alias for Firefox. Add an application only by deliberately editing that allowlist.

## Integration from the project root

```python
from executor.executor import execute_command

result = execute_command({"action": "get_cpu_usage"})
if result["success"]:
    print(result.get("data"))
else:
    print(result["error"], result["message"])
```

The future GUI/Main integration should pass structured dictionaries to `execute_command`. NLP should produce an action and its required fields; it should not produce a raw shell string.

The separate project `security/security_gate.py` currently validates **shell-command text**, whereas this executor accepts **structured action dictionaries**. They are different interfaces: do not pass an action dictionary to `validate_command`, and do not send raw shell commands to this executor. Keep the text Security Gate upstream only if that part of the pipeline is intentionally processing shell-command text; the executor still enforces its own payload and workspace protections.

## Run the optional command-line interface

From the project root:

```bash
python3 -m executor.main
```

Enter one JSON object per line. Type `exit` to quit. To confirm a dangerous action, repeat the same line starting with `!`, for example `!{"action":"delete_file","path":"a.txt"}`.

## Tests

From the project root:

```bash
python3 -m unittest executor.test_executor -v
```

These tests cover payload validation, path traversal, symlink rejection, overwrite protection, file operations, confirmation handling, and action registration. They do not test every installed desktop utility or physical device.
