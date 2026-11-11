import datetime
import os
import shutil
import subprocess
from .security import require_confirmation

def get_date_time(payload):
    del payload
    now = datetime.datetime.now().astimezone()
    return {"success": True, "message": "Current date and time retrieved.", "data": now.isoformat()}

def get_disk_usage(payload):
    path = payload.get("path", "/")
    usage = shutil.disk_usage(path)
    gib = 1024 ** 3
    data = {
        "total_gb": round(usage.total / gib, 2),
        "used_gb": round(usage.used / gib, 2),
        "free_gb": round(usage.free / gib, 2),
        "used_percent": round(usage.used / usage.total * 100, 1)
    }
    return {"success": True, "message": "Disk usage retrieved.", "data": data}

def get_memory_usage(payload):
    del payload
    # Linux /proc/meminfo avoids an extra Python dependency.
    values = {}
    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            key, rest = line.split(":", 1)
            values[key] = int(rest.strip().split()[0])  # kB
    total = values["MemTotal"]
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = total - available
    data = {
        "total_mb": round(total / 1024, 1),
        "used_mb": round(used / 1024, 1),
        "available_mb": round(available / 1024, 1),
        "used_percent": round(used / total * 100, 1)
    }
    return {"success": True, "message": "Memory usage retrieved.", "data": data}

def get_system_info(payload):
    del payload
    uname = os.uname()
    return {
        "success": True,
        "message": "System information retrieved.",
        "data": {"system": uname.sysname, "node": uname.nodename, "release": uname.release, "machine": uname.machine}
    }

def _run_system_action(command, label):
    executable = shutil.which(command[0])
    if executable is None:
        raise RuntimeError(f"Required program '{command[0]}' is not installed.")
    subprocess.Popen([executable] + command[1:], start_new_session=True)
    return {"success": True, "message": f"{label} requested."}

def lock_screen(payload):
    del payload
    return _run_system_action(["loginctl", "lock-session"], "Screen lock")

def logout(payload):
    require_confirmation(payload, "logout")
    return _run_system_action(["gnome-session-quit", "--logout", "--no-prompt"], "Logout")

def restart_system(payload):
    require_confirmation(payload, "restart_system")
    return _run_system_action(["systemctl", "reboot"], "Restart")

def shutdown_system(payload):
    require_confirmation(payload, "shutdown_system")
    return _run_system_action(["systemctl", "poweroff"], "Shutdown")
