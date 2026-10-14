# MindStack: Voice-Enhanced Linux

A voice interaction layer on top of Linux (Ubuntu). The user speaks a command, the system runs an allowed operation, and replies by voice.
The project runs on top of the Linux kernel without modifying it, and interacts with the shell and system APIs safely.

## Architecture
User -> Microphone -> Speech-to-Text -> Command Understanding -> Command Validation -> Linux Operation -> Result -> Text-to-Speech -> User

## Project Structure
| Folder | Owner | Responsibility |
|---|---|---|
| `stt/` | Dareen Hossam | Microphone input and speech-to-text |
| `nlp/` | Jody Rafik | Converting text into a known intent |
| `security/` | Rahma Saeed | Allowed-command list, delete confirmation, command validation |
| `executor/` | Shimaa Mamdouh | Running commands and handling errors |
| `tts/` | Rahma Yasser | Voice responses |
| `linux_ops/` | Salma Waheed | Files, applications, processes, and system resources |
| `gui/` | Habiba Ayman (Team leader) | User interface |
| `tests/` | Rana Said | Test cases |
| `docs/` | Everyone | Documentation and team rules |
| `main.py` | Rana Said | Main entry point |

## Installation
```bash
git clone https://github.com/salmawaheed77/MindStack.git
cd MindStack
git checkout develop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
python3 main.py
```

## Security Rule
Voice text is never executed directly as a shell command. It is first converted into a known intent, then validated, and only allowed operations are executed. Dangerous operations such as deleting files require user confirmation.

## Team Workflow
Read `docs/GIT_WORKFLOW.md` before making any commit.
