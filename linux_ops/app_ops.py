"""Open and close applications for MindStack (linux_ops).

Only applications in ALLOWED_APPS can be opened or closed.
Commands are never built from raw voice text and never run through a shell.
Each function returns a dict: {"ok": bool, "message": str, "data": any}.
"""
import shutil
import subprocess

import psutil

# friendly name -> (command to launch, process names used when closing)
ALLOWED_APPS = {
    "browser": ("firefox", ["firefox", "firefox-bin"]),
    "calculator": ("gnome-calculator", ["gnome-calculator"]),
    "text editor": ("gnome-text-editor", ["gnome-text-editor"]),
}


def _result(ok, message, data=None):
    return {"ok": ok, "message": message, "data": data}


def open_app(name):
    name = name.lower().strip()
    if name not in ALLOWED_APPS:
        return _result(False, f"{name} is not an allowed application")
    command = ALLOWED_APPS[name][0]
    if shutil.which(command) is None:
        return _result(False, f"{name} is not installed")
    subprocess.Popen(
        [command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return _result(True, f"Opened {name}")


def close_app(name):
    name = name.lower().strip()
    if name not in ALLOWED_APPS:
        return _result(False, f"{name} is not an allowed application")
    process_names = ALLOWED_APPS[name][1]
    closed = 0
    for p in psutil.process_iter(["name"]):
        if p.info["name"] in process_names:
            try:
                p.terminate()
                closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    if closed == 0:
        return _result(False, f"{name} is not running")
    return _result(True, f"Closed {name}")
