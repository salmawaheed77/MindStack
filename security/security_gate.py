"""Security validation gate. It checks commands but never executes them.

The caller MUST run the returned `argv` without a shell (shell=False).

validate_command(text) returns a dict:
    status: "ALLOW" | "WARN" | "APPROVED" | "BLOCK"
    message, command, argv, confirmation_required, confirmation_token

WARN means the user must confirm. The result carries a short-lived
`confirmation_token` bound to that exact command. After the user confirms in
the UI, call validate_command(text, confirmation_token=token) again.
"""

from __future__ import annotations

import fnmatch
import hashlib
import hmac
import os
import re
import secrets
import shlex
import time
from pathlib import Path

try:
    from .security_commands import ALLOW, WARN, BLOCK
except ImportError:  # running the file directly for a quick check
    from security_commands import ALLOW, WARN, BLOCK

MAX_COMMAND_LENGTH = 500
TOKEN_TTL_SECONDS = 60
_SECRET = secrets.token_bytes(32)  # new secret every run

PACKAGE_MANAGERS = {"apt", "apt-get", "yum", "pip", "pip3"}
FILE_MUTATING = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln", "tee",
    "chmod", "chown", "chgrp", "tar", "gzip", "gunzip", "unzip",
}
STRICT_INSIDE = {"rm", "rmdir", "mv"}            # may not target the workspace itself
NO_GLOB = {"rm", "rmdir", "mv", "chmod", "chown", "chgrp"}
PROTECTED_PROCESSES = {
    "systemd", "init", "sshd", "gdm", "gdm3", "Xorg",
    "gnome-shell", "dbus-daemon", "NetworkManager",
}


def default_workspace() -> str:
    return os.path.realpath(Path.home() / "MindStack_Workspace")


def _read_protected():
    home = os.path.realpath(Path.home())
    prefixes = [
        "/etc/shadow", "/etc/gshadow", "/etc/sudoers", "/etc/ssh", "/root",
        "/dev/mem", "/dev/kmem", "/proc/kcore",
        f"{home}/.ssh", f"{home}/.gnupg", f"{home}/.aws",
        f"{home}/.kube", f"{home}/.bash_history",
    ]
    globs = ["/proc/*/environ", "/proc/*/mem"]
    return prefixes, globs


def _result(status, message, command=None, argv=None,
            confirmation_required=False, token=None):
    return {
        "status": status,
        "message": message,
        "command": command,
        "argv": argv,
        "confirmation_required": confirmation_required,
        "confirmation_token": token,
    }


# ------------------------------------------------------------ confirmation
def _make_token(raw: str, expires: int) -> str:
    sig = hmac.new(_SECRET, f"{raw}\0{expires}".encode(), hashlib.sha256).hexdigest()
    return f"{expires}.{sig}"


def _token_valid(raw: str, token) -> bool:
    if not isinstance(token, str) or "." not in token:
        return False
    exp_text, sig = token.split(".", 1)
    try:
        expires = int(exp_text)
    except ValueError:
        return False
    if expires < time.time():
        return False
    expected = _make_token(raw, expires).split(".", 1)[1]
    return hmac.compare_digest(sig, expected)


# ----------------------------------------------------------------- helpers
def _path_candidates(args):
    """Yield values that may be paths (skips plain options like -la)."""
    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                yield arg.split("=", 1)[1]
        elif arg.startswith("-"):
            rest = arg[2:]
            if rest.startswith(("/", "~")):      # e.g. -o/etc/x
                yield rest
        else:
            yield arg


def _resolve(value: str, cwd: str) -> str:
    expanded = os.path.expanduser(value)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd, expanded)
    return os.path.realpath(expanded)   # also follows symlinks


def _is_read_protected(resolved: str) -> bool:
    prefixes, globs = _read_protected()
    return (
        any(resolved.startswith(p) for p in prefixes)
        or any(fnmatch.fnmatch(resolved, g) for g in globs)
    )


def _has_short(args, letters: str) -> bool:
    return any(
        a.startswith("-") and not a.startswith("--")
        and any(ch in a[1:] for ch in letters)
        for a in args
    )


def _has_long(args, *names) -> bool:
    return any(a == n or a.startswith(n + "=") for a in args for n in names)


def _check_arguments(command, args, root):
    """Return a reason string if the arguments are dangerous, else None."""
    positional = [a for a in args if not a.startswith("-")]

    # 1) Sensitive files can not be read by ANY command.
    for value in _path_candidates(args):
        if _is_read_protected(_resolve(value, root)):
            return "Access to a protected path is blocked."

    # 2) Mutating file commands may only touch the workspace.
    if command in FILE_MUTATING:
        for value in _path_candidates(args):
            resolved = _resolve(value, root)
            if resolved == root:
                if command in STRICT_INSIDE:
                    return "The workspace folder itself can not be modified."
            elif not resolved.startswith(root + os.sep):
                return "Modifying files outside the workspace is blocked."

    if command in NO_GLOB and any(ch in a for a in positional for ch in "*?["):
        return "Wildcards are not allowed in destructive commands."

    # 3) Per-command rules.
    if command == "find" and any(
        a in {"-exec", "-execdir", "-delete", "-ok", "-okdir",
              "-fprint", "-fprint0", "-fprintf", "-fls"} for a in args
    ):
        return "This find option can run commands or write files."
    if command == "sort" and (_has_short(args, "o") or _has_long(args, "--output", "--compress-program")):
        return "sort can not write files or run programs."
    if command == "uniq" and len(positional) > 1:
        return "uniq with an output file is blocked."
    if command == "tree" and _has_short(args, "o"):
        return "tree can not write files."
    if command == "date" and (_has_short(args, "s") or _has_long(args, "--set")):
        return "Changing the system date is blocked."
    if command == "hostname" and positional:
        return "Changing the hostname is blocked."
    if command == "tail" and (_has_short(args, "fF") or _has_long(args, "--follow")):
        return "tail --follow never ends."
    if command == "ping" and not _has_short(args, "c"):
        return "ping needs a count, for example: ping -c 3 host."
    if command == "rm" and _has_long(args, "--no-preserve-root"):
        return "--no-preserve-root is blocked."
    if command == "kill" and any(a in {"0", "1", "-1"} for a in args):
        return "Killing pid 1 / all processes is blocked."
    if command in {"killall", "pkill"} and any(a in PROTECTED_PROCESSES for a in positional):
        return "Killing a critical system process is blocked."

    if command in {"curl", "wget"}:
        for a in args:
            if "@" in a:
                return "Sending local files is blocked."
            if "://" in a and not a.lower().startswith(("http://", "https://")):
                return "Only http:// and https:// URLs are allowed."
            if a.lower().startswith("file:"):
                return "file: URLs are blocked."
        if any(a in {"-T", "-K", "-i", "-e"} for a in args) or _has_long(
            args, "--upload-file", "--config", "--post-file",
            "--input-file", "--execute",
        ):
            return "This download option is blocked."

    if command == "tar" and (
        any(a in {"-I", "-P"} for a in args)
        or _has_long(args, "--to-command", "--checkpoint-action",
                     "--use-compress-program", "--rsh-command", "--absolute-names")
    ):
        return "This tar option can run programs or write outside the workspace."

    if command in {"chmod", "chown", "chgrp"} and positional:
        mode = positional[0]
        if command == "chmod" and (
            (re.fullmatch(r"[0-7]{4}", mode) and mode[0] != "0")
            or re.search(r"[+=][rwxXt]*s", mode)
        ):
            return "setuid / setgid / sticky permissions are blocked."

    if command in PACKAGE_MANAGERS:
        if not args or args[0] != "install":
            return "Only package install commands are eligible."
        if any(a in {"-y", "--assume-yes", "--root", "-i"} for a in args) or _has_long(
            args, "--index-url", "--extra-index-url", "--trusted-host"
        ):
            return "Unattended, privileged or custom-source installation is blocked."
        if any("://" in a or a.startswith("git+") for a in args):
            return "Installing from a URL is blocked."

    return None


# -------------------------------------------------------------------- main
def validate_command(command_text, confirmation_token=None, workspace=None):
    """Classify a command string. Never executes anything."""
    if not isinstance(command_text, str) or not command_text.strip():
        return _result("BLOCK", "Empty or invalid command.")

    raw = command_text.strip()
    if len(raw) > MAX_COMMAND_LENGTH:
        return _result("BLOCK", "Command is too long.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in raw):
        return _result("BLOCK", "Control characters and new lines are forbidden.")
    if "<" in raw or ">" in raw:
        return _result("BLOCK", "Redirection is not supported. Use the executor's create_file instead.")
    if re.search(r"[|;&`$]", raw):
        return _result("BLOCK", "Shell operators, chaining and variable expansion are forbidden.")

    try:
        parts = shlex.split(raw, posix=True)
    except ValueError:
        return _result("BLOCK", "Invalid command quoting.")
    if not parts:
        return _result("BLOCK", "Empty command.")

    command, args = parts[0], parts[1:]
    if "/" in command:
        return _result("BLOCK", "Use a bare command name, not a path.")
    if command in BLOCK:
        return _result("BLOCK", f"'{command}' is forbidden by policy.")
    if command not in ALLOW and command not in WARN:
        return _result("BLOCK", f"Unknown command '{command}' is blocked by default.")

    root = os.path.realpath(workspace) if workspace else default_workspace()
    reason = _check_arguments(command, args, root)
    if reason:
        return _result("BLOCK", reason)

    if command in ALLOW:
        return _result("ALLOW", "Command is allowed.", raw, parts)

    # WARN: needs a confirmation token bound to this exact command.
    if _token_valid(raw, confirmation_token):
        return _result("APPROVED", "Command confirmed by user.", raw, parts)
    token = _make_token(raw, int(time.time()) + TOKEN_TTL_SECONDS)
    return _result(
        "WARN", f"'{command}' requires explicit user confirmation.",
        raw, parts, confirmation_required=True, token=token,
    )
