"""System information for MindStack."""

import psutil


def _result(ok, message, data=None):
    return {
        "ok": ok,
        "message": message,
        "data": data
    }


def show_processes(limit=10):
    procs = []

    try:
        for p in psutil.process_iter(
            ["pid", "name", "memory_percent"]
        ):
            try:
                info = p.info

                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "memory_percent": round(
                        info["memory_percent"] or 0, 1
                    ),
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):
                continue

        procs.sort(
            key=lambda x: x["memory_percent"],
            reverse=True
        )

        top = procs[:max(0, limit)]

        return _result(
            True,
            f"{len(procs)} processes running, "
            f"showing top {len(top)}",
            top
        )

    except Exception as e:
        return _result(False, f"Process error: {e}")


def show_usage():
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        data = {
            "cpu_percent": cpu,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / 1024**3, 1),
            "ram_total_gb": round(ram.total / 1024**3, 1),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024**3, 1),
            "disk_total_gb": round(disk.total / 1024**3, 1),
        }

        message = (
            f"CPU {cpu} percent, "
            f"RAM {ram.percent} percent, "
            f"disk {disk.percent} percent used"
        )

        return _result(True, message, data)

    except Exception as e:
        return _result(False, f"System usage error: {e}")

def show_usage():
    """Return CPU, RAM and disk usage."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    data = {
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / 1024**3, 1),
        "ram_total_gb": round(ram.total / 1024**3, 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024**3, 1),
        "disk_total_gb": round(disk.total / 1024**3, 1),
    }
    message = f"CPU {cpu} percent, RAM {ram.percent} percent, disk {disk.percent} percent used"
    return _result(True, message, data)
