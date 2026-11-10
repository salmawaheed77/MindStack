"""Security validation gate. It checks commands but never executes them."""

import re
import shlex

# Package import is preferred. The fallback also supports running this file
# directly from inside the security directory for a quick local check.
try:
    from .security_commands import ALLOW, WARN, BLOCK
except ImportError:
    from security_commands import ALLOW, WARN, BLOCK


PACKAGE_MANAGERS = {"apt", "apt-get", "yum", "pip", "pip3"}
SHELL_CONTEXT_COMMANDS = {"cd", "jobs", "history", "export", "alias"}
PROTECTED_PATHS = ("/etc", "/boot", "/dev", "/proc", "/sys")

MUTATING_COMMANDS = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln", "tee", "sed",
    "chmod", "chown", "chgrp", "kill", "killall", "pkill", "renice",
    "tar", "gzip", "gunzip", "unzip", "wget", "curl", "scp", "ftp",
    "crontab", "apt", "apt-get", "yum", "pip", "pip3",
}


def _result(status, message, command=None, confirmation_required=False):
    return {
        "status": status,
        "message": message,
        "command": command,
        "confirmation_required": confirmation_required,
    }


def _is_protected_path(value):
    if not value.startswith("/"):
        return False
    path = value.rstrip("/") or "/"
    return any(
        path == protected or path.startswith(protected + "/")
        for protected in PROTECTED_PATHS
    )


def _has_dangerous_arguments(command, args, raw):
    if command == "find":
        forbidden = {"-exec", "-execdir", "-delete", "-ok", "-okdir"}
        if any(arg in forbidden for arg in args):
            return True

    if command == "history" and "-c" in args:
        return True

    if command == "rm":
        flags = [arg for arg in args if arg.startswith("-")]
        targets = [arg for arg in args if not arg.startswith("-")]
        has_rf = any(
            len(flag) > 1 and "r" in flag[1:] and "f" in flag[1:]
            for flag in flags
        )
        if has_rf and any(target in {"/", "/*"} for target in targets):
            return True

    if command == "chmod" and "-R" in args and "777" in args and "/" in args:
        return True

    if command == "mv" and args and args[0] == "/":
        return True

    if re.search(r">\s*/dev/sda(?:\s|$)", raw):
        return True

    if command in {"nc", "ncat", "netcat"} and any(
        arg in {"-e", "-c"} for arg in args
    ):
        return True

    if "/dev/tcp/" in raw and "bash" in raw:
        return True

    if command in MUTATING_COMMANDS:
        if any(_is_protected_path(arg) for arg in args):
            return True
        if "/etc/passwd" in raw or "/etc/shadow" in raw:
            return True

    return False


def validate_command(command_text, confirmed=False):
    """Return ALLOW, WARN, APPROVED, or BLOCK for a command string.

    `confirmed=True` must only be used after the UI confirms this exact
    command with the user. This function does not run any command.
    """
    if not isinstance(command_text, str) or not command_text.strip():
        return _result("BLOCK", "Empty or invalid command.")

    raw = command_text.strip()

    # Block shell chaining, pipes, backgrounding and command substitution.
    if re.search(r"[|;&`]", raw) or "$(" in raw:
        return _result("BLOCK", "Shell operators or command chaining are forbidden.")

    # Redirection is WARN. The executor must implement it safely without a shell.
    if ">" in raw:
        if not confirmed:
            return _result(
                "WARN",
                "Redirection requires explicit user confirmation.",
                confirmation_required=True,
            )
        return _result(
            "APPROVED",
            "Redirection confirmed; executor must handle it without shell=True.",
            raw,
        )

    try:
        parts = shlex.split(raw, posix=True)
    except ValueError:
        return _result("BLOCK", "Invalid command quoting.")

    if not parts:
        return _result("BLOCK", "Empty command.")

    command = parts[0].rsplit("/", 1)[-1]
    args = parts[1:]

    if command in BLOCK:
        return _result("BLOCK", f"'{command}' is forbidden by policy.")

    if _has_dangerous_arguments(command, args, raw):
        return _result("BLOCK", "Dangerous arguments or protected path detected.")

    if command in PACKAGE_MANAGERS:
        if not args or args[0] != "install":
            return _result("BLOCK", "Only package install commands are eligible for WARN.")
        if any(arg in {"-y", "--assume-yes", "--root"} for arg in args):
            return _result("BLOCK", "Unattended or privileged installation is blocked.")

    if command in ALLOW:
        message = "Command is allowed."
        if command in SHELL_CONTEXT_COMMANDS:
            message += " Executor must handle shell context specially."
        return _result("ALLOW", message, raw)

    if command in WARN:
        if not confirmed:
            return _result(
                "WARN",
                f"'{command}' requires explicit user confirmation.",
                confirmation_required=True,
            )
        return _result("APPROVED", "Command confirmed by user.", raw)

    return _result("BLOCK", f"Unknown command '{command}' is blocked by default.")
