Text-to-Speech (TTS) Module
The TTS module converts response text into spoken audio.
Install on Ubuntu
sudo apt update
sudo apt install espeak-ng libespeak-ng1
pip install pyttsx3
Install the Python dependencies from the project's requirements file as appropriate for the environment.
Usage
From the project root:
from tts.tts import speak

speak("Hello, this is MindStack.")
Integration
The component that receives the Executor result can pass a user-friendly response message to speak(...).

Do not pass internal tracebacks or sensitive system details directly to speech output. Handle errors and empty messages before calling TTS.
Testing
Test audio output on the target Ubuntu machine. In a virtual machine, confirm that audio output is enabled in the VM settings and that Ubuntu can play audio.
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
