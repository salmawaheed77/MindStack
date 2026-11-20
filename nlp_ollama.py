import json
import ollama

MODEL = "qwen2.5:1.5b"

ACTIONS = [
    "create_folder",
    "create_file",
    "delete_file",
    "search_file",
    "open_application",
    "open_website",
    "check_system_info",
    "unknown",
]

SYSTEM_PROMPT = f"""You convert a user's computer command into JSON.
Reply with JSON only, in this exact shape:
{{"action": "<one of {ACTIONS}>", "path": "<name or path, or empty string>"}}
Use "unknown" if the command does not match any action.
Commands are always in  English."""


def understand_command(text):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        format="json",
        options={"temperature": 0},
    )
    try:
        result = json.loads(response["message"]["content"])
    except json.JSONDecodeError:
        return {"action": "unknown", "original_text": text}

    if result.get("action") not in ACTIONS:
        return {"action": "unknown", "original_text": text}
    return result


if __name__ == "__main__":
    text = input("Enter your command: ")
    print(json.dumps(understand_command(text), indent=4, ensure_ascii=False))
