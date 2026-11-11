import json
import sys
from command_executor.executor import execute_command

def main():
    print("Sound OS Command Executor")
    print("Enter one JSON command per line. Type 'exit' to quit.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.lower() == "exit":
            break
        try:
            payload = json.loads(line)
            result = execute_command(payload)
        except json.JSONDecodeError as exc:
            result = {
                "success": False,
                "error": "invalid_json",
                "message": f"Invalid JSON: {exc.msg}"
            }
        except Exception as exc:
            result = {
                "success": False,
                "error": "internal_error",
                "message": str(exc)
            }
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
