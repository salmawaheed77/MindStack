"""Payload validation and workspace boundary enforcement for the executor."""

from __future__ import annotations

import os
from pathlib import Path

WORKSPACE = (Path.home() / "MindStack_Workspace").resolve()


def ensure_private_workspace(path: Path = None) -> Path:
    """Create the workspace and make it readable/writable by the owner only (700)."""
    path = path or WORKSPACE
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass  # not the owner / unsupported filesystem: keep going
    return path


ensure_private_workspace()


class ConfirmationRequiredError(PermissionError):
    """Raised when an operation needs explicit approval from the user."""


CONFIRMED_KEY = "_confirmed"  # set by execute_command only, never read from upstream


def validate_payload(payload: object) -> dict:
    """Check the payload and return a clean copy.

    "confirmed" and any key starting with "_" are removed: approval must come
    from the user through execute_command(..., confirmed=True), never from the
    NLP model or any other upstream data.
    """
    if not isinstance(payload, dict):
        raise ValueError("The command must be a JSON object.")

    action = payload.get("action")
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Missing or invalid 'action'.")

    # The executor accepts structured actions only, never shell text.
    forbidden_fields = {"command", "shell", "shell_command", "cmd"}
    supplied = forbidden_fields.intersection(payload)
    if supplied:
        raise PermissionError(
            "Raw shell commands are not accepted by the executor. "
            "Send a supported structured action instead."
        )
    return {k: v for k, v in payload.items()
            if k != "confirmed" and not (isinstance(k, str) and k.startswith("_"))}


def safe_path(user_path: object) -> Path:
    """Resolve a path inside WORKSPACE and reject traversal and symlinks.

    Rejecting symlink components prevents a path inside the workspace from
    redirecting file operations to a location outside it.
    """
    if not isinstance(user_path, str) or not user_path.strip():
        raise ValueError("A non-empty file path is required.")
    if "\x00" in user_path:
        raise ValueError("File paths cannot contain a null character.")

    raw = Path(user_path).expanduser()
    candidate = raw if raw.is_absolute() else WORKSPACE / raw
    candidate = Path(os.path.abspath(candidate))

    try:
        relative = candidate.relative_to(WORKSPACE)
    except ValueError as exc:
        raise PermissionError(
            f"File operations are restricted to {WORKSPACE}."
        ) from exc

    # Check every existing component without following symlinks.
    current = WORKSPACE
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise PermissionError("Symbolic links are not allowed in file paths.")
        except OSError as exc:
            raise PermissionError(f"Unable to validate path: {exc}") from exc

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(WORKSPACE)
    except ValueError as exc:
        raise PermissionError(
            f"File operations are restricted to {WORKSPACE}."
        ) from exc
    return resolved


def require_confirmation(payload: dict, operation: str) -> None:
    if payload.get(CONFIRMED_KEY) is not True:
        raise ConfirmationRequiredError(
            f"'{operation}' requires explicit user confirmation. "
            "Ask the user, then call execute_command again with confirmed=True."
        )
