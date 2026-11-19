Linux Operations — Implemented in the Executor
Architecture note: MindStack does not contain or require a separate linux_ops/ package. All supported Linux and computer operations are implemented through the executor/ package.

Where the operations live
See [`../executor/README.md`](../executor/README.md) for the detailed Executor documentation, supported action names, safety rules, integration contract, and test commands.

The Executor is responsible for:
- File and folder operations
- Application management
- Browser operations
- System information and process management
- Session and system actions
- Device controls such as volume, brightness, and Wi-Fi
Workspace
File operations use the workspace configured by the current Executor implementation:
~/MindStack_Workspace
Use paths relative to this workspace. Do not assume the old ~/voice_workspace location is still used.
Testing
Run the Executor tests from the project root:
python3 -m unittest executor.test_executor -v
The old test_linux_ops.py imports from linux_ops and should be updated to test the actual executor/ implementation instead. Do not create a placeholder linux_ops/ package just to make those old imports pass.
Integration rule
Other components should send structured action dictionaries to the Executor. They should not import modules from a nonexistent linux_ops/ package or execute arbitrary shell commands from recognized voice text.
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
