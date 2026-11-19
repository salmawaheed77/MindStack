"""Structured action dispatcher for the MindStack project.

The executor deliberately does not interpret natural language and never runs
arbitrary shell commands. The upstream pipeline should convert an intent into
one of the supported action dictionaries below.
"""

from __future__ import annotations

import logging
import os
import subprocess

from . import app_manager, browser_manager, device_manager, file_manager, system_manager
from .security import CONFIRMED_KEY, ConfirmationRequiredError, validate_payload

log = logging.getLogger("mindstack.executor")

HANDLERS = {
    # Applications
    "open_application": app_manager.open_application,
    "close_application": app_manager.close_application,
    "list_running_applications": app_manager.list_running_applications,
    # Files and folders
    "create_folder": file_manager.create_folder,
    "create_file": file_manager.create_file,
    "read_file": file_manager.read_file,
    "copy_file": file_manager.copy_file,
    "move_file": file_manager.move_file,
    "rename_file": file_manager.rename_file,
    "delete_file": file_manager.delete_file,
    "delete_folder": file_manager.delete_folder,
    "search_files": file_manager.search_files,
    "list_files": file_manager.list_files,
    # Browser
    "open_website": browser_manager.open_website,
    "google_search": browser_manager.google_search,
    # System information and controls
    "get_date_time": system_manager.get_date_time,
    "get_cpu_usage": system_manager.get_cpu_usage,
    "get_disk_usage": system_manager.get_disk_usage,
    "get_memory_usage": system_manager.get_memory_usage,
    "get_processes": system_manager.get_processes,
    "get_system_info": system_manager.get_system_info,
    "lock_screen": system_manager.lock_screen,
    "logout": system_manager.logout,
    "restart_system": system_manager.restart_system,
    "shutdown_system": system_manager.shutdown_system,
    # Device controls
    "volume_up": device_manager.volume_up,
    "volume_down": device_manager.volume_down,
    "volume_mute": device_manager.volume_mute,
    "brightness_up": device_manager.brightness_up,
    "brightness_down": device_manager.brightness_down,
    "wifi_on": device_manager.wifi_on,
    "wifi_off": device_manager.wifi_off,
}


def get_supported_actions() -> list[str]:
    """Return supported action names in a stable, sorted order."""
    return sorted(HANDLERS)


def _friendly(exc: Exception) -> str:
    """A short message that sounds fine when spoken: no errno codes, no full paths."""
    if getattr(exc, "errno", None) is not None:  # raised by the OS itself
        name = os.path.basename(str(exc.filename)) if getattr(exc, "filename", None) else ""
        return f"{exc.strerror}: {name}" if name else str(exc.strerror)
    return str(exc)


def execute_command(payload: object, *, confirmed: bool = False) -> dict:
    """Validate and execute one structured action, returning a result dict.

    `confirmed=True` is how the user's approval reaches the executor. It is a
    separate argument on purpose: a "confirmed" field inside `payload` (for
    example one produced by the AI model) is ignored.
    """
    try:
        command = validate_payload(payload)
        action = command["action"].strip()
        handler = HANDLERS.get(action)
        if handler is None:
            return {"success": False, "error": "unsupported_action", "message": f"Action '{action}' is not supported."}

        command[CONFIRMED_KEY] = confirmed is True
        log.info("execute %s (confirmed=%s)", action, command[CONFIRMED_KEY])
        result = handler(command)
        if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
            return {"success": False, "error": "invalid_handler_result", "message": f"Handler for '{action}' returned an invalid result."}
        return result

    except ConfirmationRequiredError as exc:
        return {"success": False, "error": "confirmation_required", "confirmation_required": True, "message": str(exc)}
    except PermissionError as exc:
        return {"success": False, "error": "permission_denied", "message": _friendly(exc)}
    except ValueError as exc:
        return {"success": False, "error": "validation_error", "message": str(exc)}
    except FileNotFoundError as exc:
        return {"success": False, "error": "not_found", "message": _friendly(exc)}
    except FileExistsError as exc:
        return {"success": False, "error": "already_exists", "message": _friendly(exc)}
    except IsADirectoryError as exc:
        return {"success": False, "error": "is_a_directory", "message": _friendly(exc)}
    except NotADirectoryError as exc:
        return {"success": False, "error": "not_a_directory", "message": _friendly(exc)}
    except UnicodeDecodeError:
        return {"success": False, "error": "encoding_error", "message": "The file is not valid UTF-8 text."}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout", "message": "The system command took too long."}
    except Exception as exc:
        log.exception("unexpected error in %s", payload.get("action") if isinstance(payload, dict) else "?")
        return {"success": False, "error": "execution_error", "message": _friendly(exc)}
