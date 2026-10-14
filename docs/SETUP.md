# Setup Guide

Follow these steps to prepare your machine for the MindStack project.

## 1. Install Ubuntu
Use Ubuntu 22.04 or newer. Recommended options:
- A VirtualBox VM (2+ CPU cores, 4 GB+ RAM, 25 GB+ disk).
- Or dual boot.

## 2. VirtualBox only: Guest Additions
```bash
sudo apt update
sudo apt install -y build-essential dkms linux-headers-$(uname -r)
```
Then in VirtualBox: Devices -> Insert Guest Additions CD image, open the CD folder in a terminal and run:
```bash
sudo sh ./VBoxLinuxAdditions.run
systemctl reboot -i
```
After reboot: Devices -> Shared Clipboard -> Bidirectional.

## 3. Microphone and audio (VirtualBox)
1. Shut down the VM.
2. VirtualBox -> Settings -> Audio: enable Audio Output and Audio Input.
3. In Windows: Settings -> Privacy & security -> Microphone: allow desktop apps.
4. Start the VM and test:
```bash
sudo apt install -y alsa-utils
arecord -l
arecord -f S16_LE -r 16000 -c 1 -d 5 test.wav && aplay test.wav
```
You should hear your own voice.

## 4. Get the project
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git clone https://github.com/salmawaheed77/MindStack.git
cd MindStack
git checkout develop
bash setup.sh
source venv/bin/activate
```
When pushing, GitHub asks for a username and a Personal Access Token (not your password).
Create one at: GitHub -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic) -> scope: repo.

## 5. Create your branch
```bash
git checkout -b feature/your-module
```
Examples: `feature/stt`, `feature/nlp`, `feature/security`, `feature/executor`, `feature/tts`, `feature/gui`, `feature/tests`.
See `docs/GIT_WORKFLOW.md` for the full workflow.

## Troubleshooting
- Linux is case sensitive: `VBox_GAs` is not `VBox_Gas`. Press Tab to auto-complete names.
- Paste in the terminal with Ctrl+Shift+V.
- If `sudo reboot` is refused, use `systemctl reboot -i`.
- No sound input: check Audio Input in VirtualBox and the microphone permission in Windows.
