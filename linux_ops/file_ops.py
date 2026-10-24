"""File and folder operations for MindStack (linux_ops).

Every operation is restricted to the workspace folder (~/voice_workspace),
so a voice command can never touch system folders.
Each function returns a dict: {"ok": bool, "message": str, "data": any}.
"""
from functools import wraps
from pathlib import Path

WORKSPACE = Path.home() / "voice_workspace"
WORKSPACE.mkdir(exist_ok=True)


def _result(ok, message, data=None):
    return {"ok": ok, "message": message, "data": data}


def _safe_path(name):
    """Return the real path of `name` inside the workspace, or raise PermissionError."""
    root = WORKSPACE.resolve()
    path = (root / name).resolve()
    if path != root and root not in path.parents:
        raise PermissionError("Path is outside the workspace")
    return path


def _guard(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionError:
            return _result(False, "Not allowed: outside the workspace")
        except OSError as e:
            return _result(False, f"Operation failed: {e.strerror}")
    return wrapper


@_guard
def list_files(folder=""):
    path = _safe_path(folder)
    if not path.is_dir():
        return _result(False, "Folder not found")
    names = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
    return _result(True, f"Found {len(names)} items", names)


@_guard
def create_file(name):
    path = _safe_path(name)
    if path.exists():
        return _result(False, "File already exists")
    path.touch()
    return _result(True, f"File {name} created")


@_guard
def create_folder(name):
    path = _safe_path(name)
    if path.exists():
        return _result(False, "Folder already exists")
    path.mkdir(parents=True)
    return _result(True, f"Folder {name} created")


@_guard
def rename_file(old_name, new_name):
    src = _safe_path(old_name)
    dst = _safe_path(new_name)
    if not src.exists():
        return _result(False, "File not found")
    if dst.exists():
        return _result(False, "A file with the new name already exists")
    src.rename(dst)
    return _result(True, f"Renamed {old_name} to {new_name}")


@_guard
def delete_file(name, confirmed=False):
    """Delete a file. Needs confirmed=True (confirmation comes from the security module)."""
    path = _safe_path(name)
    if not path.is_file():
        return _result(False, "File not found")
    if not confirmed:
        return _result(False, f"Confirmation required to delete {name}")
    path.unlink()
    return _result(True, f"File {name} deleted")
