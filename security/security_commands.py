"""MindStack command permission lists (command names only).

Anything that is NOT in ALLOW or WARN is blocked by default.
Shell builtins (cd, jobs, history, help, export, alias) are not listed:
they have no effect when commands are run without a shell.
Pagers / interactive programs (less, more, man, top) are not listed because
they can spawn a shell. `env` is not listed because `env <cmd>` runs <cmd>.
"""

ALLOW = {
    # Navigation and display
    "ls", "pwd", "tree",
    # Read files
    "cat", "head", "tail", "wc", "file", "stat",
    # Search and filtering
    "grep", "sort", "uniq", "diff", "find",
    # System information
    "whoami", "id", "date", "cal", "uname", "hostname", "uptime",
    "df", "du", "free", "ps",
    # Utilities
    "which", "echo", "clear",
}

WARN = {
    # File modifications (restricted to the workspace by the gate)
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln", "tee",
    # Permissions
    "chmod", "chown", "chgrp",
    # Processes
    "kill", "killall", "pkill", "renice",
    # Compression
    "tar", "gzip", "gunzip", "unzip",
    # Network (http/https only, checked by the gate)
    "wget", "curl", "ping",
    # Scheduling / package installation
    "crontab", "apt", "apt-get", "yum", "pip", "pip3",
}

BLOCK = {
    # Shutdown and reboot
    "shutdown", "reboot", "halt", "poweroff", "init", "telinit",
    # Disks and filesystems
    "mkfs", "fdisk", "parted", "dd", "wipefs", "shred", "mount", "umount",
    # Users and privileges
    "sudo", "su", "passwd", "useradd", "userdel", "usermod",
    "groupadd", "visudo",
    # Kernel and services
    "insmod", "rmmod", "modprobe", "systemctl", "service", "chroot",
    # Firewall
    "iptables", "ufw",
    # Dynamic execution, shells and interpreters
    "eval", "exec", "bash", "sh", "zsh", "fish", "dash",
    "python", "python3", "perl", "ruby", "node", "awk", "sed",
    # Remote access / raw network tools
    "ssh", "scp", "ftp", "sftp", "nc", "ncat", "netcat", "socat", "telnet",
    # Wrappers that run another command
    "env", "xargs", "nohup", "timeout", "watch", "nice",
}
