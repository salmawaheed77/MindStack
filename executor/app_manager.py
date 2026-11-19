"""Allowlisted desktop application launching and closing."""

import shutil
import subprocess

# Friendly name -> (executable, process name).
# "terminal" and "code" are intentionally NOT allowed: they give the user a shell,
# which would bypass the "no shell" rule of this project.
# The Linux kernel truncates process names ("comm") to 15 characters, and
# `pkill -x` / `ps -o comm=` only see the truncated name, so always compare
# with _comm(process_name).
APPS = {
    "calculator": ("gnome-calculator", "gnome-calculator"),
    "firefox": ("firefox", "firefox"),
    "browser": ("firefox", "firefox"),
    "web_browser": ("firefox", "firefox"),
    "files": ("nautilus", "nautilus"),
    "file_manager": ("nautilus", "nautilus"),
    "text_editor": ("gedit", "gedit"),
    "gedit": ("gedit", "gedit"),
    "gnome_text_editor": ("gnome-text-editor", "gnome-text-editor"),
    "vlc": ("vlc", "vlc"),
    "libreoffice": ("libreoffice", "soffice"),
}

# If the first program is not installed, try these (newer Ubuntu has no gedit).
FALLBACKS = {
    "text_editor": [("gnome-text-editor", "gnome-text-editor")],
}


COMM_MAX = 15


def _comm(process_name):
    """Name as the kernel reports it (max 15 characters)."""
    return process_name[:COMM_MAX]


def _candidates(key):
    return [APPS[key]] + FALLBACKS.get(key, [])


def _get_app(target):
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Please provide an application target.")
    key = target.strip().casefold().replace(" ", "_")
    if key not in APPS:
        raise ValueError(
            f"'{target}' is not in the allowed application list. "
            f"Allowed apps: {', '.join(sorted(APPS))}"
        )
    return key, APPS[key]


def open_application(payload: dict) -> dict:
    key, (executable, _) = _get_app(payload.get("target"))
    path = None
    for candidate_exe, _proc in _candidates(key):
        path = shutil.which(candidate_exe)
        if path:
            break
    if path is None:
        names = ", ".join(exe for exe, _ in _candidates(key))
        return {"success": False, "error": "application_not_installed", "message": f"{key} is allowed but none of these is installed: {names}."}
    try:
        subprocess.Popen([path], start_new_session=True, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return {"success": False, "error": "application_launch_failed", "message": str(exc)}
    return {"success": True, "message": f"Opening {key}."}


def close_application(payload: dict) -> dict:
    key, _ = _get_app(payload.get("target"))
    pkill = shutil.which("pkill")
    if pkill is None:
        raise RuntimeError("pkill is not available on this system.")
    last_error = ""
    for _exe, process_name in _candidates(key):
        result = subprocess.run([pkill, "-x", _comm(process_name)], capture_output=True, text=True, check=False, timeout=10)
        if result.returncode == 0:
            return {"success": True, "message": f"Close signal sent to {key}."}
        if result.returncode != 1:
            last_error = result.stderr.strip() or "Unable to close the application."
    if last_error:
        return {"success": False, "error": "close_failed", "message": last_error}
    return {"success": False, "error": "not_running", "message": f"{key} is not running."}


def list_running_applications(payload: dict) -> dict:
    del payload
    ps = shutil.which("ps")
    if ps is None:
        raise RuntimeError("The 'ps' utility is not installed.")
    result = subprocess.run([ps, "-eo", "comm="], capture_output=True, text=True, check=True, timeout=10)
    running = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    # ps shows the kernel's 15-character name, so compare with _comm() but
    # report the full, readable process name.
    full_names = {proc for key in APPS for _, proc in _candidates(key)}
    known = sorted(name for name in full_names if _comm(name) in running)
    return {"success": True, "message": "Running applications retrieved.", "data": known}
