"""Catalogue of supported voice commands (shown on the Commands page).

Each entry: (name, example phrase, description, needs_confirmation)
Keep this in sync with what the command-understanding module really supports.
"""

COMMAND_CATALOG = [
    ("Files", [
        ("List files", "list files",
         "Shows the files in the current folder.", False),
        ("Create file", "create file notes",
         "Creates an empty file.", False),
        ("Create folder", "create folder projects",
         "Creates a new folder.", False),
        ("Rename file", "rename file notes to ideas",
         "Renames an existing file.", False),
        ("Delete file", "delete file notes",
         "Deletes a file. Always asks for confirmation first.", True),
    ]),
    ("Applications", [
        ("Open application", "open browser",
         "Launches an application by name.", False),
        ("Close application", "close browser",
         "Closes a running application.", False),
    ]),
    ("Processes", [
        ("Show processes", "show processes",
         "Lists the running processes.", False),
    ]),
    ("System information", [
        ("CPU usage", "show cpu usage",
         "Reads the current CPU load.", False),
        ("RAM usage", "show ram usage",
         "Reads the current memory usage.", False),
        ("Disk usage", "show disk usage",
         "Reads the used disk space.", False),
    ]),
]
