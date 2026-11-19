Git Workflow
Branches
- main: final submission only.
- develop: shared integration branch.
- Each team member should work on a feature branch related to their assigned component.
Suggested branch names:
- feature/stt
- feature/security
- feature/executor
- feature/tts
- feature/gui
- feature/tests
- docs/update
There is no separate linux-ops branch or linux_ops/ component: Linux and computer operations are implemented in executor/.
Steps
1. Get the latest changes:
   git checkout develop
   git pull
2. Create a branch:
   git checkout -b feature/your-component
3. Work primarily in the files belonging to your assigned component. Coordinate before changing shared interfaces or another component's files.
4. Review your changes:
   git status
   git diff
5. Commit:
   git add .
   git commit -m "Describe the change"
6. Push your branch:
   git push -u origin feature/your-component
7. Open a Pull Request into develop and request a teammate review.
Rules
- Do not push directly to develop or main.
- Do not commit the venv/ directory, temporary audio files, caches, or local secrets.
- Use clear commit messages.
- Add required Python packages to the appropriate requirements.txt.
- Coordinate changes to interfaces between the GUI, STT/TTS, security components, and Executor.
- The Executor's public interface uses structured action dictionaries. Do not replace this with arbitrary shell-command strings without an agreed design change.
