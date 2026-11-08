"""Security gate for Linux commands received as text from the AI/NLP module.

This module DOES NOT execute commands. It returns a structured decision for
the Command Executor:
    ALLOW     - command may be passed to the executor
    WARN      - user confirmation is required
    APPROVED  - WARN command has a confirmation token from the caller
    BLOCK     - command must not be executed

The caller must obtain real user consent before calling validate_command()
again with confirmed=True. Never infer consent from speech transcription alone.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

from security_commands import ALLOW, WARN, BLOCK


SHELL_META_PATTERN = re.compile(r"[|;&`<>]")
COMMAND_SUBSTITUTION_PATTERN = re.compile(r"\$\s*\(")
SENSITIVE_PATHS = (
    "/etc",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
)

# These commands can modify files, permissions, processes, or the environment.
MUTATING_COMMANDS = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln", "tee", "sed",
    "chmod", "chown", "chgrp", "kill", "killall", "pkill", "renice",
    "tar", "gzip", "gunzip", "unzip", "wget", "curl", "scp", "ftp",
    "export", "alias", "crontab", "apt", "apt-get", "yum", "pip", "pip3",
}

PACKAGE_MANAGERS = {"apt", "apt-get", "yum", "pip", "pip3"}
PACKAGE_INSTALL_WORDS = {"install"}

# Shell built-ins whose behavior depends on the current interactive shell.
SHELL_CONTEXT_COMMANDS = {"cd", "jobs", "history", "export", "alias"}

def _result(status: str, message: str, command: str | None = None,
            confirmation_required: bool = False) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "command": command,
        "confirmation_required": confirmation_required,
    }


def _is_sensitive_path(value: str) -> bool:
    """Return True for absolute paths inside protected system locations."""
    normalized = value.rstrip("/") or "/"
    return any(
        normalized == root or normalized.startswith(root + "/")
        for root in SENSITIVE_PATHS
    )


def _has_dangerous_find_options(args: list[str]) -> bool:
    forbidden = {"-exec", "-execdir", "-delete", "-ok", "-okdir"}
    return any(arg in forbidden or arg.startswith("-exec=") for arg in args)


def _has_dangerous_patterns(command_text: str, command: str,
                             args: list[str]) -> bool:
    compact = " ".join([command] + args)

    # Explicit destructive patterns from the project policy.
    if re.search(r"(^|\s)rm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\s+(/|\*|/\*)(?:\s|$)", compact):
        return True
    if re.search(r"(^|\s)chmod\s+-R\s+777\s+/(?:\s|$)", compact):
        return True
    if re.search(r"(^|\s)mv\s+/\s+", compact):
        return True
    if re.search(r">\s*/dev/sda(?:\s|$)", command_text):
        return True
    if re.search(r"nc\s+.*(?:-e|-c)", compact):
        return True
    if re.search(r"bash\s+-i\s+.*?/dev/tcp/", compact):
        return True
    if ":(){ :|:& };:" in command_text.replace(" ", ""):
        return True

    # Block attempts to target protected system locations with mutating commands.
    if command in MUTATING_COMMANDS:
        for arg in args:
            if _is_sensitive_path(arg):
                return True

    return False


def validate_command(command_text: str, confirmed: bool = False) -> dict[str, Any]:
    """Validate a command string and return a structured security decision.

    `confirmed=True` must only be supplied after the UI has collected explicit
    user confirmation for this exact command.
    """
    if not isinstance(command_text, str) or not command_text.strip():
        return _result("BLOCK", "Empty or invalid command.")

    original = command_text.strip()

    # Do not accept multiple commands, pipes, shell expansions, or redirection
    # as ordinary executable command strings.
    if SHELL_META_PATTERN.search(original) or COMMAND_SUBSTITUTION_PATTERN.search(original):
        # Redirection is categorized as WARN in the project policy, but it
        # must be handled by a dedicated, restricted executor operation.
        if re.search(r">>", original) or re.search(r"(?<!>)>(?!>)", original):
            if confirmed:
                return _result(
                    "APPROVED",
                    "Redirection confirmed; executor must handle it without a shell.",
                    original,
                    False,
                )
            return _result(
                "WARN",
                "Redirection requires explicit confirmation and safe handling.",
                None,
                True,
            )
        return _result("BLOCK", "Shell operators and command chaining are not allowed.")

    try:
        parts = shlex.split(original, posix=True)
    except ValueError:
        return _result("BLOCK", "Invalid command quoting.")

    if not parts:
        return _result("BLOCK", "Empty command.")

    command = parts[0].rsplit("/", 1)[-1]
    args = parts[1:]

    # Block shell interpreters and scripting runtimes as command launchers.
    if command in BLOCK:
        return _result("BLOCK", f"'{command}' is forbidden by the security policy.")

    if _has_dangerous_patterns(original, command, args):
        return _result("BLOCK", "Dangerous command or protected path detected.")

    if command == "find" and _has_dangerous_find_options(args):
        return _result("BLOCK", "find with -exec, -delete, or -ok is forbidden.")

    if command in PACKAGE_MANAGERS:
        if not args or args[0] not in PACKAGE_INSTALL_WORDS:
            return _result("BLOCK", "Only package install commands are eligible for WARN.")
        # Explicitly block privilege escalation in arguments.
        if any(arg in {"sudo", "--root", "--assume-yes"} for arg in args):
            return _result("BLOCK", "Privileged or unattended package operation blocked.")

    if command == "history" and "-c" in args:
        return _result("BLOCK", "Clearing command history is forbidden.")

    if command == "sed" and "-i" in args:
        pass  # Still WARN, but never ALLOW.

    if command in ALLOW:
        # These shell-context commands cannot be safely run as ordinary
        # child processes. The executor must implement them specially.
        if command in SHELL_CONTEXT_COMMANDS:
            return _result(
                "ALLOW",
                f"'{command}' is allowed; executor must handle shell context safely.",
                original,
            )
        return _result("ALLOW", "Command is allowed.", original)

    if command in WARN:
        if not confirmed:
            return _result(
                "WARN",
                f"'{command}' requires explicit user confirmation.",
                None,
                True,
            )
        return _result(
            "APPROVED",
            f"'{command}' approved after confirmation.",
            original,
            False,
        )

    return _result("BLOCK", f"Unknown command '{command}' is blocked by default.")
