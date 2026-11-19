MindStack GUI (PySide6)
The MindStack GUI is the graphical interface for the Sound Operating System project. It displays system state, recognized or typed commands, execution results, and command history.
Run
From this directory:
pip install -r requirements.txt
python3 main.py
On Ubuntu, the GUI may require:
sudo apt update
sudo apt install python3-pip libxcb-cursor0
The GUI currently includes a MockBackend for demonstration and a RealBackend integration layer. A mock backend simulates responses; it does not prove that an operation was executed by Ubuntu.

Before a full system demonstration, verify that the application is configured to use the real backend and that the real backend calls the project components correctly.
Screens
Screen / dialog	File
Home (status, command, result, CPU/RAM/disk)	app/pages/home_page.py
Command log (search, filters, sorting, CSV export)	app/pages/log_page.py
Commands (supported command catalogue and examples)	app/pages/commands_page.py
Settings (microphone, language, voice, security, theme)	app/pages/settings_page.py
Confirmation dialog	app/dialogs/confirm_dialog.py
Microphone test dialog	app/dialogs/mic_test_dialog.py
About dialog	app/dialogs/about_dialog.py
Main window and system tray	app/main_window.py


Keyboard shortcuts are displayed in the application where available.
Main GUI structure
main.py
app/
  backend.py          Backend interface and mock backend
  real_backend.py     Integration backend
  controller.py       GUI/backend coordination
  models.py           Command history and settings models
  state.py            UI states
  theme.py            Dark and light themes
  commands_data.py    GUI command catalogue
  main_window.py      Main application window
  pages/
  dialogs/
  widgets/
Integration with the Executor
The GUI should communicate through its backend and controller rather than calling Linux commands directly from UI widgets.

The real integration path should pass structured action dictionaries to the Executor, for example:
{"action": "get_cpu_usage"}
The Executor is the single project component responsible for supported file, application, browser, system, and device operations. There is no separate linux_ops/ module.

Confirm that the real backend handles the Executor's success, error, and confirmation-required results. Dangerous actions must not be confirmed automatically.
Responsiveness
Long-running work, microphone capture, STT, TTS, and system operations should not block the Qt event loop. Use an appropriate worker/thread approach and communicate results back to the UI safely.
Notes
- The command log and settings are handled by the GUI application code.
- A mock backend is useful for interface development but should not be presented as proof of end-to-end execution.
- Test microphone and device features on the actual Ubuntu environment where the project will be demonstrated.QSettings`.
- لو شغّلتيه على سيرفر من غير صوت (CI) ضيفي `MINDSTACK_SKIP_AUDIO=1` عشان تتجنبي فحص أجهزة الصوت.
- الواجهة والأوامر والنتائج كلها بالإنجليزي. لغة التعرف على الصوت الافتراضية English، وتقدري تغيّريها من Settings.
