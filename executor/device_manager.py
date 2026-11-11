import shutil
import subprocess

def _run_first_available(candidates, args, success_message):
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            result = subprocess.run([executable] + args, capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "message": success_message}
            return {"success": False, "error": "device_command_failed", "message": result.stderr.strip() or result.stdout.strip()}
    raise RuntimeError(f"None of these tools is installed: {', '.join(candidates)}")

def volume_up(payload):
    del payload
    if shutil.which("wpctl"):
        return _run_first_available(["wpctl"], ["set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"], "Volume increased.")
    return _run_first_available(["pactl"], ["set-sink-volume", "@DEFAULT_SINK@", "+5%"], "Volume increased.")

def volume_down(payload):
    del payload
    if shutil.which("wpctl"):
        return _run_first_available(["wpctl"], ["set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"], "Volume decreased.")
    return _run_first_available(["pactl"], ["set-sink-volume", "@DEFAULT_SINK@", "-5%"], "Volume decreased.")

def volume_mute(payload):
    del payload
    if shutil.which("wpctl"):
        return _run_first_available(["wpctl"], ["set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], "Mute toggled.")
    return _run_first_available(["pactl"], ["set-sink-mute", "@DEFAULT_SINK@", "toggle"], "Mute toggled.")

def brightness_up(payload):
    del payload
    return _run_first_available(["brightnessctl"], ["set", "+5%"], "Brightness increased.")

def brightness_down(payload):
    del payload
    return _run_first_available(["brightnessctl"], ["set", "5%-"], "Brightness decreased.")

def wifi_on(payload):
    del payload
    return _run_first_available(["nmcli"], ["radio", "wifi", "on"], "Wi-Fi enabled.")

def wifi_off(payload):
    del payload
    return _run_first_available(["nmcli"], ["radio", "wifi", "off"], "Wi-Fi disabled.")
