MindStack — Executor
The Executor is the project's central layer for Linux and computer operations. All supported operations are implemented in this directory; there is no separate linux_ops/ module.

It accepts structured action dictionaries, validates them, runs the corresponding operation, and returns a result. It is not a general-purpose shell and should not receive arbitrary shell strings.
Main files
- executor.py: action dispatcher and public execute_command(...) interface.
- file_manager.py: workspace file and folder operations.
- app_manager.py: allowlisted application operations.
- browser_manager.py: website opening and search.
- system_manager.py: system information, process, session, and system operations.
- device_manager.py: volume, brightness, and Wi-Fi operations.
- security.py: Executor-side safety checks.
- main.py: optional JSON-line CLI.
- test_executor.py: automated tests.
Requirements
- Python 3.10+
- Ubuntu/Linux for Linux-specific system and process information.
- Optional system utilities depending on the operation: ps, pkill, loginctl, systemctl, nmcli, wpctl or pactl, and brightnessctl.
- The relevant desktop applications must be installed for application-launching actions.
Common packages:
sudo apt update
sudo apt install procps util-linux network-manager
Optional brightness utility:
sudo apt install brightnessctl
Workspace and file safety
File operations are restricted to ~/MindStack_Workspace. The Executor creates this workspace with owner-only permissions where supported.

Example payloads:
{"action": "create_folder", "path": "College"}
{"action": "create_file", "path": "College/notes.txt", "content": "My notes"}
{"action": "read_file", "path": "College/notes.txt"}
Use paths relative to the workspace. The Executor rejects paths that escape the workspace and rejects symbolic-link components. It protects existing destinations from accidental overwrite.
Confirmation
Deleting files/folders and logging out, restarting, or shutting down require explicit user approval.
from executor.executor import execute_command

result = execute_command({
    "action": "delete_file",
    "path": "College/notes.txt"
})

if result.get("confirmation_required"):
    # Ask the user to approve this exact action.
    result = execute_command(
        {"action": "delete_file", "path": "College/notes.txt"},
        confirmed=True
    )
Only pass confirmed=True after the user has approved the exact action. Do not allow the command-understanding component to approve its own action.
Supported actions
Category	Actions
Applications	open_application, close_application, list_running_applications
Files	create_folder, create_file, read_file, copy_file, move_file, rename_file, delete_file, delete_folder, search_files, list_files
Browser	open_website, google_search
System	get_date_time, get_cpu_usage, get_disk_usage, get_memory_usage, get_processes, get_system_info, lock_screen, logout, restart_system, shutdown_system
Devices	volume_up, volume_down, volume_mute, brightness_up, brightness_down, wifi_on, wifi_off


Application names are controlled by the allowlist in app_manager.py. Add applications only by deliberately updating that allowlist.
Integration
from executor.executor import execute_command

result = execute_command({"action": "get_cpu_usage"})

if result.get("success"):
    print(result.get("data"))
else:
    print(result.get("error"), result.get("message"))
The upstream command-understanding component should provide the action name and required fields as a dictionary. The GUI should communicate through its backend/controller layer.

The separate security/ package has a different interface from the Executor. Do not pass an Executor action dictionary to a shell-text validator or pass raw shell text to the Executor. If both components are used in the final pipeline, implement and test an explicit integration adapter.
CLI
From the project root:
python3 -m executor.main
The CLI accepts one JSON object per line. Type exit to quit.
Tests
From the project root:
python3 -m unittest executor.test_executor -v
These tests do not replace testing on the target Ubuntu desktop. Some operations depend on installed utilities, desktop applications, hardware, and permissions.ysical device.
