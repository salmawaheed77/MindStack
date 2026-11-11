import shutil
import subprocess

# Applications are deliberately allowlisted. Add more installed apps here.
# Each entry: user-friendly name -> executable, process name.
APPS = {
    "calculator": ("gnome-calculator", "gnome-calculator"),
    "firefox": ("firefox", "firefox"),
    "files": ("nautilus", "nautilus"),
    "text_editor": ("gedit", "gedit"),
    "gedit": ("gedit", "gedit"),
    "terminal": ("gnome-terminal", "gnome-terminal"),
    "vlc": ("vlc", "vlc"),
    "libreoffice": ("libreoffice", "soffice"),
    "code": ("code", "code"),
}

def _get_app(target):
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Please provide an application target.")
    key = target.strip().lower().replace(" ", "_")
    if key not in APPS:
        raise ValueError(
            f"'{target}' is not in the allowed application list. "
            f"Allowed apps: {', '.join(APPS.keys())}"
        )
    return key, APPS[key]

def open_application(payload):
    key, (executable, _) = _get_app(payload.get("target"))
    path = shutil.which(executable)
    if path is None:
        return {
            "success": False,
            "error": "application_not_installed",
            "message": f"{key} is allowed but '{executable}' is not installed."
        }
    subprocess.Popen([path], start_new_session=True)
    return {"success": True, "message": f"Opening {key}."}

def close_application(payload):
    key, (_, process_name) = _get_app(payload.get("target"))
    pkill = shutil.which("pkill")
    if pkill is None:
        raise RuntimeError("pkill is not available on this system.")
    result = subprocess.run(
        [pkill, "-x", process_name],
        capture_output=True, text=True, check=False
    )
    if result.returncode == 0:
        return {"success": True, "message": f"Close signal sent to {key}."}
    if result.returncode == 1:
        return {"success": False, "error": "not_running", "message": f"{key} is not running."}
    return {"success": False, "error": "close_failed", "message": result.stderr.strip()}

def list_running_applications(payload):
    del payload
    ps = shutil.which("ps")
    result = subprocess.run(
        [ps, "-eo", "comm="], capture_output=True, text=True, check=True
    )
    running = sorted(set(line.strip() for line in result.stdout.splitlines() if line.strip()))
    known = sorted({proc for _, proc in APPS.values() if proc in running})
    return {"success": True, "message": "Running applications retrieved.", "data": known}
