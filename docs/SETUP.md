Setup Guide
This guide prepares an Ubuntu/Linux environment for MindStack. The project can be tested in an Ubuntu virtual machine; a dual-boot installation is not required.
1. Ubuntu environment
Use Ubuntu 22.04 or newer.

Suggested VirtualBox resources:
- 2 or more CPU cores
- 4 GB RAM or more
- 25 GB disk or more
Make sure the VM has working network and audio input/output if you plan to test voice features.
2. Optional VirtualBox Guest Additions
Install build dependencies:
sudo apt update
sudo apt install -y build-essential dkms linux-headers-$(uname -r)
In VirtualBox, choose Devices → Insert Guest Additions CD Image, open the mounted CD directory in a terminal, and run the installer:
sudo sh ./VBoxLinuxAdditions.run
Restart Ubuntu after installation. Shared Clipboard can then be enabled from the VirtualBox Devices menu.
3. Microphone and audio
For a VirtualBox VM:
1. Shut down the VM.
2. Open VirtualBox VM Settings → Audio.
3. Enable audio input and output.
4. In the host operating system, allow desktop applications to access the microphone.
5. Start Ubuntu and install the audio utilities:
sudo apt update
sudo apt install -y alsa-utils
List recording devices:
arecord -l
Record and play a short test:
arecord -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav
Remove the temporary recording when finished:
rm test.wav
4. Get the project and install dependencies
git clone https://github.com/salmawaheed77/MindStack.git
cd MindStack
git checkout develop
bash setup.sh
source venv/bin/activate
If you are setting up an existing local copy rather than cloning, open a terminal in the project root and run the setup script there.
5. Optional Executor system utilities
The Executor uses Ubuntu/Linux utilities for some system and device actions. Install the common packages:
sudo apt update
sudo apt install -y procps util-linux network-manager
For brightness control, if needed:
sudo apt install -y brightnessctl
Volume control may use PipeWire (wpctl) or PulseAudio (pactl), depending on the Ubuntu installation.
6. Run the project
Activate the environment:
source venv/bin/activate
Run the project entry point:
python3 main.py
Run the Executor CLI separately:
python3 -m executor.main
Run Executor tests:
python3 -m unittest executor.test_executor -v
For GUI-specific instructions, read:

gui/mindstack_gui_english/mindstack_gui/README.md
7. Git identity and branches
Set your Git identity if it has not already been configured:
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
Create a feature branch before editing:
git checkout -b feature/your-component
See docs/GIT_WORKFLOW.md for the full team workflow.
Troubleshooting
- Linux paths and filenames are case-sensitive.
- Paste into a Linux terminal with Ctrl+Shift+V in many desktop terminal applications.
- If the microphone is not detected, check VirtualBox audio input settings and host microphone permissions.
- If a device action fails, check whether the required system utility is installed and whether the current user has permission.
- Run commands from the project root when using module commands such as python3 -m executor.main.
- Linux is case sensitive: `VBox_GAs` is not `VBox_Gas`. Press Tab to auto-complete names.
- Paste in the terminal with Ctrl+Shift+V.
- If `sudo reboot` is refused, use `systemctl reboot -i`.
- No sound input: check Audio Input in VirtualBox and the microphone permission in Windows.
