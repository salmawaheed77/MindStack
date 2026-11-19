"""Workspace-only file operations used by the MindStack executor."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import security
from .security import require_confirmation, safe_path

MAX_READ_BYTES = 1_000_000
MAX_SEARCH_RESULTS = 200


def _folder_arg(payload: dict) -> str:
    """The NLP layer may send folder="" or null; both mean the workspace root."""
    folder = payload.get("folder")
    return folder if isinstance(folder, str) and folder.strip() else "."


def create_folder(payload: dict) -> dict:
    path = safe_path(payload.get("path"))
    existed = path.exists()
    if existed and not path.is_dir():
        raise FileExistsError(f"'{path.name}' already exists and is a file, not a folder.")
    path.mkdir(parents=True, exist_ok=True)
    return {
        "success": True,
        "message": f"Folder already exists: {path.name}" if existed else f"Folder created: {path.name}",
        "data": {"path": str(path.relative_to(security.WORKSPACE)), "already_existed": existed},
    }


def create_file(payload: dict) -> dict:
    content = payload.get("content", "")
    if not isinstance(content, str):
        raise ValueError("'content' must be text.")
    path = safe_path(payload.get("path"))
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation avoids silently replacing an existing file.
    try:
        with path.open("x", encoding="utf-8", newline="") as stream:
            stream.write(content)
    except FileExistsError:
        raise FileExistsError(f"'{path.name}' already exists.") from None
    return {"success": True, "message": f"File created: {path.name}", "data": {"path": str(path.relative_to(security.WORKSPACE))}}


def read_file(payload: dict) -> dict:
    path = safe_path(payload.get("path"))
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError(f"'{path.name}' is a folder, not a file.")
        raise FileNotFoundError(f"'{path.name}' was not found.")
    size = path.stat().st_size
    if size > MAX_READ_BYTES:
        raise ValueError(f"File is too large to read (limit: {MAX_READ_BYTES // 1_000_000} MB).")
    content = path.read_text(encoding="utf-8")
    return {"success": True, "message": "File read successfully.", "data": content}


def _ensure_destination_is_new(destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(
            f"'{destination.name}' already exists. Choose a different destination; "
            "the executor never overwrites existing files."
        )


def copy_file(payload: dict) -> dict:
    source = safe_path(payload.get("source"))
    destination = safe_path(payload.get("destination"))
    if not source.is_file():
        if source.is_dir():
            raise IsADirectoryError("copy_file accepts files only, not folders.")
        raise FileNotFoundError(f"'{source.name}' was not found.")
    if source == destination:
        raise ValueError("Source and destination must be different paths.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _ensure_destination_is_new(destination)
    shutil.copy2(source, destination)
    return {"success": True, "message": f"Copied {source.name} to {destination.name}.", "data": {"destination": str(destination.relative_to(security.WORKSPACE))}}


def move_file(payload: dict) -> dict:
    source = safe_path(payload.get("source"))
    destination = safe_path(payload.get("destination"))
    if not source.is_file():
        if source.is_dir():
            raise IsADirectoryError("move_file accepts files only, not folders.")
        raise FileNotFoundError(f"'{source.name}' was not found.")
    if source == destination:
        raise ValueError("Source and destination must be different paths.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _ensure_destination_is_new(destination)
    shutil.move(str(source), str(destination))
    return {"success": True, "message": f"Moved {source.name} to {destination.name}.", "data": {"destination": str(destination.relative_to(security.WORKSPACE))}}


def rename_file(payload: dict) -> dict:
    source = safe_path(payload.get("path"))
    new_name = payload.get("new_name")
    if (
        not isinstance(new_name, str)
        or not new_name.strip()
        or new_name in {".", ".."}
        or "/" in new_name
        or "\\" in new_name
        or "\x00" in new_name
    ):
        raise ValueError("'new_name' must be a simple file or folder name.")
    if not source.exists():
        raise FileNotFoundError(f"'{source.name}' was not found.")
    destination = safe_path(str((source.parent / new_name).relative_to(security.WORKSPACE)))
    if source == destination:
        raise ValueError("The new name is the same as the current name.")
    _ensure_destination_is_new(destination)
    source.rename(destination)
    return {"success": True, "message": f"Renamed to {new_name}.", "data": {"path": str(destination.relative_to(security.WORKSPACE))}}


def delete_file(payload: dict) -> dict:
    require_confirmation(payload, "delete_file")
    path = safe_path(payload.get("path"))
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError(f"'{path.name}' is a folder, not a file.")
        raise FileNotFoundError(f"'{path.name}' was not found.")
    path.unlink()
    return {"success": True, "message": f"Deleted file: {path.name}"}


def delete_folder(payload: dict) -> dict:
    require_confirmation(payload, "delete_folder")
    path = safe_path(payload.get("path"))
    if not path.is_dir():
        if path.exists():
            raise NotADirectoryError(f"'{path.name}' is not a folder.")
        raise FileNotFoundError(f"'{path.name}' was not found.")
    if path == security.WORKSPACE:
        raise PermissionError("The workspace root cannot be deleted.")
    shutil.rmtree(path)
    return {"success": True, "message": f"Deleted folder: {path.name}"}


def search_files(payload: dict) -> dict:
    root = safe_path(_folder_arg(payload))
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A search query is required.")
    if not root.is_dir():
        raise NotADirectoryError(f"'{root.name}' is not a folder.")

    matches: list[str] = []
    query_lower = query.casefold()
    for item in root.rglob("*"):
        # Do not traverse or report symlinks as regular workspace content.
        if item.is_symlink():
            continue
        if query_lower in item.name.casefold():
            matches.append(str(item.relative_to(security.WORKSPACE)))
            if len(matches) >= MAX_SEARCH_RESULTS:
                break
    return {"success": True, "message": f"Found {len(matches)} matching item(s).", "data": matches}


def list_files(payload: dict) -> dict:
    folder = safe_path(_folder_arg(payload))
    if not folder.is_dir():
        if folder.exists():
            raise NotADirectoryError(f"'{folder.name}' is not a folder.")
        raise FileNotFoundError(f"'{folder.name}' was not found.")

    items = []
    for path in folder.iterdir():
        if path.is_symlink():
            item_type = "symlink"
        elif path.is_dir():
            item_type = "folder"
        else:
            item_type = "file"
        items.append({"name": path.name, "type": item_type})
    items.sort(key=lambda item: (item["type"] != "folder", item["name"].casefold()))
    return {"success": True, "message": "Folder contents retrieved.", "data": items}
