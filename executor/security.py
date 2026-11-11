from pathlib import Path

# All file-management operations are restricted to this folder.
WORKSPACE = (Path.home() / "SoundOS_Workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("The command must be a JSON object.")
    action = payload.get("action")
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Missing or invalid 'action'.")
    # Prevent accidental execution of arbitrary shell commands.
    if "command" in payload or "shell" in payload:
        raise PermissionError("Raw shell commands are not accepted.")

def safe_path(user_path):
    if not isinstance(user_path, str) or not user_path.strip():
        raise ValueError("A non-empty file path is required.")
    candidate = (WORKSPACE / user_path).resolve()
    try:
        candidate.relative_to(WORKSPACE)
    except ValueError:
        raise PermissionError("File operations are restricted to ~/SoundOS_Workspace.")
    return candidate

def require_confirmation(payload, operation):
    if payload.get("confirmed") is not True:
        raise PermissionError(
            f"'{operation}' requires user confirmation. Repeat the request with confirmed=true "
            "only after the user has explicitly approved it."
        )
