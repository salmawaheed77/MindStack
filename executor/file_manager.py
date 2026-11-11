import shutil
from .security import safe_path, require_confirmation

MAX_READ_BYTES = 1_000_000

def create_folder(payload):
    path = safe_path(payload.get("path"))
    path.mkdir(parents=True, exist_ok=True)
    return {"success": True, "message": f"Folder created: {path.name}"}

def create_file(payload):
    path = safe_path(payload.get("path"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"{path.name} already exists.")
    content = payload.get("content", "")
    if not isinstance(content, str):
        raise ValueError("'content' must be text.")
    path.write_text(content, encoding="utf-8")
    return {"success": True, "message": f"File created: {path.name}"}

def read_file(payload):
    path = safe_path(payload.get("path"))
    if not path.is_file():
        raise FileNotFoundError(path.name)
    if path.stat().st_size > MAX_READ_BYTES:
        raise ValueError("File is too large to read (limit: 1 MB).")
    return {"success": True, "message": "File read successfully.", "data": path.read_text(encoding="utf-8")}

def copy_file(payload):
    source = safe_path(payload.get("source"))
    destination = safe_path(payload.get("destination"))
    if not source.is_file():
        raise FileNotFoundError(source.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {"success": True, "message": f"Copied {source.name} to {destination.name}."}

def move_file(payload):
    source = safe_path(payload.get("source"))
    destination = safe_path(payload.get("destination"))
    if not source.exists():
        raise FileNotFoundError(source.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return {"success": True, "message": f"Moved {source.name} to {destination.name}."}

def rename_file(payload):
    source = safe_path(payload.get("path"))
    new_name = payload.get("new_name")
    if not isinstance(new_name, str) or not new_name.strip() or "/" in new_name:
        raise ValueError("'new_name' must be a simple file or folder name.")
    destination = safe_path(str(source.parent.relative_to(safe_path("."))) + "/" + new_name)
    if not source.exists():
        raise FileNotFoundError(source.name)
    source.rename(destination)
    return {"success": True, "message": f"Renamed to {new_name}."}

def delete_file(payload):
    require_confirmation(payload, "delete_file")
    path = safe_path(payload.get("path"))
    if not path.is_file():
        raise FileNotFoundError(path.name)
    path.unlink()
    return {"success": True, "message": f"Deleted file: {path.name}"}

def delete_folder(payload):
    require_confirmation(payload, "delete_folder")
    path = safe_path(payload.get("path"))
    if not path.is_dir():
        raise FileNotFoundError(path.name)
    if path == safe_path("."):
        raise PermissionError("The workspace root cannot be deleted.")
    shutil.rmtree(path)
    return {"success": True, "message": f"Deleted folder: {path.name}"}

def search_files(payload):
    root = safe_path(payload.get("folder", "."))
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A search query is required.")
    if not root.is_dir():
        raise NotADirectoryError(root)
    matches = []
    for item in root.rglob("*"):
        if query.lower() in item.name.lower():
            matches.append(str(item.relative_to(safe_path("."))))
            if len(matches) >= 200:
                break
    return {"success": True, "message": f"Found {len(matches)} matching item(s).", "data": matches}

def list_files(payload):
    folder = safe_path(payload.get("folder", "."))
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    items = sorted(
        [{"name": p.name, "type": "folder" if p.is_dir() else "file"} for p in folder.iterdir()],
        key=lambda item: (item["type"] != "folder", item["name"].lower())
    )
    return {"success": True, "message": "Folder contents retrieved.", "data": items}
