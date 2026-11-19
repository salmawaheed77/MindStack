MindStack — Sound Operating System
MindStack is a voice-controlled system for Ubuntu/Linux. It receives a user's spoken request, converts it into a structured action, validates that action, executes supported operations through the Executor, and can return the result through Text-to-Speech.

The project uses the existing Linux operating system. It does not replace or modify the Linux kernel.
Architecture
User
  ↓
Microphone
  ↓
Speech-to-Text (STT)
  ↓
Command understanding
  ↓
Structured action
  ↓
Executor (validation + operation handling)
  ↓
Execution result
  ↓
Text-to-Speech (TTS)
  ↓
User

GUI ↔ Backend / Controller ↔ Project components
Important design decision: All supported computer and Linux operations are handled inside executor/. There is no separate linux_ops/ module in this project.
Main project folders
Path	Responsibility
stt/	Speech-to-Text input
tts/	Text-to-Speech responses
executor/	Validates structured actions and performs file, application, browser, system, and device operations
security/	Separate security-related command validation components; coordinate their use with the Executor interface
gui/	PySide6 graphical interface
tests/	Automated tests
docs/	Setup, architecture, and team workflow documentation
main.py	Project-level entry point


The command-understanding component may be developed or run separately. The Executor expects a structured action dictionary; it does not accept arbitrary shell text as an instruction.
Installation
Use Ubuntu 22.04 or newer.
git clone https://github.com/salmawaheed77/MindStack.git
cd MindStack
git checkout develop
bash setup.sh
source venv/bin/activate
See [`docs/SETUP.md`](docs/SETUP.md) for detailed setup instructions and optional Ubuntu packages.
Running
From the project root, activate the virtual environment first.
python3 main.py
To run the Executor's command-line interface:
python3 -m executor.main
To run the GUI, follow the instructions in
[`gui/mindstack_gui_english/mindstack_gui/README.md`](gui/mindstack_gui_english/mindstack_gui/README.md).
Executor safety
The Executor accepts structured actions such as:
{"action": "get_cpu_usage"}
It does not execute arbitrary shell commands from voice text. File operations are restricted to the ~/MindStack_Workspace directory. Destructive and system-critical actions require explicit confirmation through the Executor's confirmation argument.

Read [`executor/README.md`](executor/README.md) for the supported action list, safety rules, and tests.
Tests
Run the Executor tests from the project root:
python3 -m unittest executor.test_executor -v
Other tests should be run only when their required modules and hardware dependencies are available. See the relevant test file before running it.
Team workflow
Read [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) before creating branches or submitting changes.
## Speech-to-Text (stt)
Requires ffmpeg. Download it, extract it, and place the folder at `stt/ffmpeg/` so that `stt/ffmpeg/bin/ffmpeg.exe` exists.
