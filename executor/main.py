"""Optional line-oriented CLI for manually exercising the executor.

Run from the project root with: python3 -m executor.main
"""

import json
import sys

from .executor import execute_command


def main() -> None:
    print("MindStack Command Executor")
    print("Enter one JSON command per line. Type 'exit' to quit.")
    print("Dangerous actions ask for confirmation: repeat the same line starting with '!' to confirm.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.casefold() == "exit":
            break
        confirmed = line.startswith("!")
        try:
            payload = json.loads(line[1:] if confirmed else line)
            result = execute_command(payload, confirmed=confirmed)
        except json.JSONDecodeError as exc:
            result = {"success": False, "error": "invalid_json", "message": f"Invalid JSON: {exc.msg}"}
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
