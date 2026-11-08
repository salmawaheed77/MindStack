"""
Ubuntu Linux Security Command Lists
Contains command names only, grouped by policy level.
No command parsing, execution, NLP, or extra modules.
"""

ALLOW = {
    # Navigation and display
    "ls", "pwd", "cd", "tree",

    # Read files
    "cat", "head", "tail", "less", "more", "wc", "file", "stat",

    # Search and filtering
    "grep", "sort", "uniq", "diff", "find",

    # System information
    "whoami", "id", "date", "cal", "uname", "hostname",
    "uptime", "df", "du", "free", "env",

    # Process display
    "ps", "top", "jobs",

    # Help and utilities
    "man", "help", "which", "history", "echo", "clear",
}

WARN = {
    # File modifications
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln",
    "tee", "sed",

    # Permissions
    "chmod", "chown", "chgrp",

    # Processes
    "kill", "killall", "pkill", "renice",

    # Compression
    "tar", "gzip", "gunzip", "unzip",

    # Network
    "wget", "curl", "ssh", "scp", "ftp", "ping",

    # Configuration
    "export", "alias", "crontab",

    # Package installation
    "apt", "apt-get", "yum", "pip", "pip3",
}

BLOCK = {
    # Shutdown and reboot
    "shutdown", "reboot", "halt", "poweroff", "init", "telinit",

    # Disks and filesystems
    "mkfs", "fdisk", "parted", "dd", "wipefs", "shred",
    "mount", "umount",

    # Users and privileges
    "sudo", "su", "passwd", "useradd", "userdel", "usermod",
    "groupadd", "visudo",

    # Kernel and services
    "insmod", "rmmod", "modprobe", "systemctl", "service", "chroot",

    # Firewall
    "iptables", "ufw",

    # Dynamic execution and shells/interpreters
    "eval", "exec", "bash", "sh", "zsh", "fish",
    "python", "python3", "perl", "ruby", "node",

    # Network tools that can provide raw/listener access
    "nc", "ncat", "netcat", "socat",
}


def classify(command: str) -> str:
    """Return ALLOW, WARN, or BLOCK for a command name."""
    name = command.strip().split("/")[-1]

    if name in BLOCK:
        return "BLOCK"
    if name in WARN:
        return "WARN"
    if name in ALLOW:
        return "ALLOW"
    return "BLOCK"  # Default deny for unknown commands


if __name__ == "__main__":
    print("ALLOW:", ", ".join(sorted(ALLOW)))
    print("\\nWARN:", ", ".join(sorted(WARN)))
    print("\\nBLOCK:", ", ".join(sorted(BLOCK)))

    print("\\nExample checks:")
    for item in ("ls", "rm", "sudo", "unknown_command"):
        print(f"{item}: {classify(item)}")
