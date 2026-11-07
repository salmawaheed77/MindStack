# linux_ops Module

Linux operations for MindStack. The Executor calls these functions after the intent has been validated.

## Safe workspace
File operations only work inside `~/voice_workspace`. Any path outside it is rejected.
The folder permissions are `700`, so only the owner can read or write in it.

## Return format
Every function returns the same dict:
```python
{"ok": True or False, "message": "text that can be spoken", "data": result or None}
```

## File operations (`linux_ops/file_ops.py`)
| Function | Description |
|---|---|
| `list_files(folder="")` | List files and folders. `data` is a list of names. |
| `create_file(name)` | Create an empty file. |
| `create_folder(name)` | Create a folder. |
| `rename_file(old_name, new_name)` | Rename a file or folder. |
| `delete_file(name, confirmed=False)` | Delete a file. Needs `confirmed=True`, otherwise it returns "Confirmation required". |

## System information (`linux_ops/system_info.py`)
| Function | Description |
|---|---|
| `show_processes(limit=10)` | Top running processes by memory. `data` is a list of `{pid, name, memory_percent}`. |
| `show_usage()` | CPU, RAM and disk usage in `data`. |

## Applications (`linux_ops/app_ops.py`)
| Function | Description |
|---|---|
| `open_app(name)` | Open an allowed application. |
| `close_app(name)` | Close an allowed application. |

Allowed names: `browser`, `calculator`, `text editor`. Anything else is rejected.
No command is ever run through a shell.

## Suggested intent mapping
| Intent | Function |
|---|---|
| `LIST_FILES` | `list_files` |
| `CREATE_FILE` | `create_file` |
| `CREATE_FOLDER` | `create_folder` |
| `RENAME_FILE` | `rename_file` |
| `DELETE_FILE` | `delete_file` |
| `OPEN_APPLICATION` | `open_app` |
| `CLOSE_APPLICATION` | `close_app` |
| `SHOW_PROCESSES` | `show_processes` |
| `SHOW_USAGE` | `show_usage` |

## Example
```python
from linux_ops import file_ops

result = file_ops.create_file("notes.txt")
print(result["message"])   # File notes.txt created
```

## Tests
```bash
python3 -m unittest tests.test_linux_ops -v
```
