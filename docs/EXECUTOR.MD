Executor — Linux and Computer Operations
Purpose
The executor/ directory is the single implementation area for supported Linux and computer operations in MindStack. The project does not use a separate linux_ops/ directory.

The Executor receives a structured action dictionary, validates it, runs the corresponding supported operation, and returns a result.
Main files
File	Responsibility
executor.py	Main dispatch point and public execute_command(...) function
file_manager.py	Workspace file and folder operations
app_manager.py	Opening, closing, and listing allowed applications
browser_manager.py	Opening websites and performing web searches
system_manager.py	System information, processes, session and system actions
device_manager.py	Volume, brightness, and Wi-Fi operations
security.py	Executor-side validation and safety checks
main.py	Optional command-line interface
test_executor.py	Executor automated tests


Return values
The Executor returns a dictionary. Successful operations include success: True; unsuccessful operations include success: False and error information.

Example:
from executor.executor import execute_command

result = execute_command({"action": "get_cpu_usage"})
print(result)
Workspace and file safety
File operations are restricted to:
~/MindStack_Workspace
Use relative paths inside that workspace where possible. The Executor checks paths to prevent escaping the workspace and rejects symbolic-link path components. Existing destinations are not overwritten by operations that enforce destination protection.

Example actions:
{"action": "create_folder", "path": "College"}
{"action": "create_file", "path": "College/notes.txt", "content": "My notes"}
{"action": "read_file", "path": "College/notes.txt"}
{"action": "list_files", "folder": ""}
Confirmation for dangerous actions
Deleting files or folders, logging out, restarting, and shutting down require explicit approval.
result = execute_command({
    "action": "delete_file",
    "path": "College/notes.txt"
})
If confirmation is required, the result indicates that confirmation is needed. After the user approves that exact action, call the Executor again with confirmed=True:
result = execute_command(
    {"action": "delete_file", "path": "College/notes.txt"},
    confirmed=True
)
Do not let the command-understanding component approve its own dangerous action. Do not set confirmed=True automatically.
Supported action groups
Category	Actions
Applications	open_application, close_application, list_running_applications
Files	create_folder, create_file, read_file, copy_file, move_file, rename_file, delete_file, delete_folder, search_files, list_files
Browser	open_website, google_search
System	get_date_time, get_cpu_usage, get_disk_usage, get_memory_usage, get_processes, get_system_info, lock_screen, logout, restart_system, shutdown_system
Devices	volume_up, volume_down, volume_mute, brightness_up, brightness_down, wifi_on, wifi_off


Actual success can depend on installed desktop applications, system utilities, permissions, and the Ubuntu desktop environment.
Optional system packages
Some actions rely on system utilities. Install only the packages needed on the target Ubuntu machine:
sudo apt update
sudo apt install procps util-linux network-manager
Optional brightness control:
sudo apt install brightnessctl
Audio controls may use wpctl (PipeWire) or pactl (PulseAudio), depending on the system.
Integration contract
The component that understands the user's request should pass a structured dictionary to the Executor:
action = {"action": "get_memory_usage"}
result = execute_command(action)
Do not pass raw voice text or arbitrary shell commands as the action. The GUI should call the project backend/controller, and the backend should connect to the actual project components according to the agreed interface.

The separate files under security/ have their own interface. Do not assume they accept the same input as execute_command; connect them only through an explicitly implemented and tested adapter if needed.
Run the command-line interface
From the project root:
python3 -m executor.main
Run Executor tests
From the project root:
python3 -m unittest executor.test_executor -v
The tests cover Executor behavior, but they do not prove that every desktop utility or physical device works on every Ubuntu machine. Test hardware- and environment-dependent actions on the target machine.
