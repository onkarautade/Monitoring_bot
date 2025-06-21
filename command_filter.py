# command_filter.py

SAFE_COMMANDS = [
    "uptime",
    "df",
    "free",
    "top",
    "ip",
    "whoami",
    "uname",
    "ls",
    "cat",
    "ping",
    "vcgencmd",
    "journalctl",
    "ps",
    "lsblk",
    "date",
    "hostname",
    "systemctl",
    "ifconfig"
]

def is_safe_command(cmd: str) -> bool:
    """Returns True if the command is in the safe whitelist."""
    first_word = cmd.strip().split()[0]
    return first_word in SAFE_COMMANDS
