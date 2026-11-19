"""Read-only system information and explicitly-confirmed power actions."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
import shutil
import subprocess
import time

from .security import require_confirmation


def get_date_time(payload: dict) -> dict:
    del payload
    now = datetime.datetime.now().astimezone()
    return {"success": True, "message": "Current date and time retrieved.", "data": now.isoformat()}


def get_disk_usage(payload: dict) -> dict:
    path = payload.get("path", "/")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("'path' must be a non-empty directory path.")
    usage = shutil.disk_usage(path)
    gib = 1024 ** 3
    data = {
        "total_gb": round(usage.total / gib, 2),
        "used_gb": round(usage.used / gib, 2),
        "free_gb": round(usage.free / gib, 2),
        "used_percent": round(usage.used / usage.total * 100, 1) if usage.total else 0.0,
    }
    return {"success": True, "message": "Disk usage retrieved.", "data": data}


def get_memory_usage(payload: dict) -> dict:
    del payload
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        raise RuntimeError("Memory information is unavailable; this action requires Linux.")
    values = {}
    with meminfo.open(encoding="utf-8") as stream:
        for line in stream:
            key, rest = line.split(":", 1)
            values[key] = int(rest.strip().split()[0])  # kB
    total = values.get("MemTotal")
    if not total:
        raise RuntimeError("MemTotal is missing from /proc/meminfo.")
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = total - available
    data = {
        "total_mb": round(total / 1024, 1),
        "used_mb": round(used / 1024, 1),
        "available_mb": round(available / 1024, 1),
        "used_percent": round(used / total * 100, 1),
    }
    return {"success": True, "message": "Memory usage retrieved.", "data": data}


def _read_cpu_counters() -> tuple[int, int]:
    with open("/proc/stat", encoding="utf-8") as stream:
        first_line = stream.readline()
    fields = first_line.split()
    if not fields or fields[0] != "cpu" or len(fields) < 5:
        raise RuntimeError("CPU statistics are unavailable in /proc/stat.")
    values = [int(value) for value in fields[1:]]
    # Linux exposes guest/guest_nice separately, but those ticks are already
    # included in user/nice; exclude them to avoid double-counting CPU time.
    total_values = values[:8]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(total_values), idle


def get_cpu_usage(payload: dict) -> dict:
    """Calculate total CPU utilization over a short sampling interval."""
    del payload
    if not Path("/proc/stat").is_file():
        raise RuntimeError("CPU usage is available only on Linux systems exposing /proc/stat.")
    total_before, idle_before = _read_cpu_counters()
    time.sleep(0.15)
    total_after, idle_after = _read_cpu_counters()
    total_delta = total_after - total_before
    idle_delta = idle_after - idle_before
    if total_delta <= 0:
        percent = 0.0
    else:
        percent = (1 - idle_delta / total_delta) * 100
    percent = max(0.0, min(100.0, percent))
    return {"success": True, "message": "CPU usage retrieved.", "data": {"used_percent": round(percent, 1)}}


def _read_total_memory_bytes() -> int:
    with open("/proc/meminfo", encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("MemTotal is missing from /proc/meminfo.")


def get_processes(payload: dict) -> dict:
    """List the top processes by memory use (default 10) without invoking a shell.

    Optional payload fields:
      limit   - how many processes to return, 1..100 (default 10)
      sort_by - "memory" (default) or "pid"
    """
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        raise RuntimeError("Process information is available only on Linux systems exposing /proc.")

    limit = payload.get("limit", 10)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("'limit' must be a whole number between 1 and 100.")
    sort_by = payload.get("sort_by", "memory")
    if sort_by not in ("memory", "pid"):
        raise ValueError("'sort_by' must be 'memory' or 'pid'.")

    total_bytes = _read_total_memory_bytes()
    page_size = os.sysconf("SC_PAGE_SIZE")
    processes = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat_text = (entry / "stat").read_text(encoding="utf-8")
            # comm is parenthesized and may itself contain spaces or ')' characters.
            closing = stat_text.rfind(")")
            if closing < 0:
                continue
            name = stat_text[stat_text.find("(") + 1:closing]
            fields = stat_text[closing + 2:].split()
            if len(fields) < 2:
                continue
            resident_pages = int((entry / "statm").read_text(encoding="utf-8").split()[1])
            memory_percent = round(resident_pages * page_size / total_bytes * 100, 1)
            processes.append({
                "pid": int(entry.name),
                "name": name,
                "state": fields[0],
                "ppid": int(fields[1]),
                "memory_percent": memory_percent,
            })
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError, OSError):
            # Processes can exit or become inaccessible while /proc is scanned.
            continue

    if sort_by == "memory":
        processes.sort(key=lambda item: (-item["memory_percent"], item["pid"]))
    else:
        processes.sort(key=lambda item: item["pid"])
    top = processes[:limit]
    return {
        "success": True,
        "message": f"{len(processes)} processes running, showing top {len(top)}.",
        "data": top,
    }


def get_system_info(payload: dict) -> dict:
    del payload
    uname = os.uname()
    return {
        "success": True,
        "message": "System information retrieved.",
        "data": {"system": uname.sysname, "node": uname.nodename, "release": uname.release, "machine": uname.machine},
    }


def _run_system_action(command: list[str], label: str) -> dict:
    executable = shutil.which(command[0])
    if executable is None:
        raise RuntimeError(f"Required program '{command[0]}' is not installed.")
    proc = subprocess.Popen([executable, *command[1:]], start_new_session=True, close_fds=True,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        # A command that is refused (no permission, no session) exits quickly with an error.
        _, err = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        return {"success": True, "message": f"{label} requested."}  # still running: the system is acting on it
    if proc.returncode != 0:
        lines = (err or "").strip().splitlines()
        return {"success": False, "error": "system_command_failed",
                "message": lines[-1] if lines else f"{label} failed (exit code {proc.returncode})."}
    return {"success": True, "message": f"{label} requested."}


def lock_screen(payload: dict) -> dict:
    del payload
    return _run_system_action(["loginctl", "lock-session"], "Screen lock")


def logout(payload: dict) -> dict:
    require_confirmation(payload, "logout")
    return _run_system_action(["gnome-session-quit", "--logout", "--no-prompt"], "Logout")


def restart_system(payload: dict) -> dict:
    require_confirmation(payload, "restart_system")
    return _run_system_action(["systemctl", "reboot"], "Restart")


def shutdown_system(payload: dict) -> dict:
    require_confirmation(payload, "shutdown_system")
    return _run_system_action(["systemctl", "poweroff"], "Shutdown")
