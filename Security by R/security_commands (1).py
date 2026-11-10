"""MindStack command permission lists."""

ALLOW = {
    "ls", "pwd", "cd", "tree",
    "cat", "head", "tail", "less", "more", "wc", "file", "stat",
    "grep", "sort", "uniq", "diff", "find",
    "whoami", "id", "date", "cal", "uname", "hostname", "uptime",
    "df", "du", "free", "env",
    "ps", "top", "jobs",
    "man", "help", "which", "history", "echo", "clear",
}

WARN = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "ln", "tee", "sed",
    "chmod", "chown", "chgrp",
    "kill", "killall", "pkill", "renice",
    "tar", "gzip", "gunzip", "unzip",
    "wget", "curl", "ssh", "scp", "ftp", "ping",
    "export", "alias", "crontab",
    "apt", "apt-get", "yum", "pip", "pip3",
}

BLOCK = {
    "shutdown", "reboot", "halt", "poweroff", "init", "telinit",
    "mkfs", "fdisk", "parted", "dd", "wipefs", "shred", "mount", "umount",
    "sudo", "su", "passwd", "useradd", "userdel", "usermod",
    "groupadd", "visudo",
    "insmod", "rmmod", "modprobe", "systemctl", "service", "chroot",
    "iptables", "ufw",
    "eval", "exec",
}
