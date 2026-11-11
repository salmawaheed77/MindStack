from . import app_manager, browser_manager, device_manager, file_manager, system_manager
from .security import validate_payload

def execute_command(payload):
    """
    Main entry point.
    Input: a dictionary received from the AI layer.
    Output: a dictionary with success/message and optional data.
    """
    try:
        validate_payload(payload)
        action = payload["action"]

        handlers = {
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
            "get_disk_usage": system_manager.get_disk_usage,
            "get_memory_usage": system_manager.get_memory_usage,
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

        handler = handlers.get(action)
        if handler is None:
            return {
                "success": False,
                "error": "unsupported_action",
                "message": f"Action '{action}' is not supported."
            }

        return handler(payload)

    except (ValueError, PermissionError) as exc:
        return {"success": False, "error": "validation_error", "message": str(exc)}
    except FileNotFoundError as exc:
        return {"success": False, "error": "not_found", "message": str(exc)}
    except Exception as exc:
        return {"success": False, "error": "execution_error", "message": str(exc)}
