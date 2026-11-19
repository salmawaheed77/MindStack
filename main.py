"""MindStack main entry point.

Pipeline:
    Microphone -> stt -> nlp (your AI model) -> executor -> tts

Usage (run from the project root, inside the venv):
    python3 main.py                    voice mode: press Enter, speak, get a spoken answer
    python3 main.py --text             typed mode: type commands, no microphone needed
    python3 main.py "list files"       run one typed command and exit
    python3 main.py --gui              start the PySide6 GUI with the real backend
    python3 main.py --no-tts           print answers instead of speaking them

The NLP / AI model is NOT part of this file. main.py only expects this module:

    nlp/intent.py
        def understand(text: str) -> dict

`understand` must return one structured executor action, for example:
    {"action": "open_application", "target": "browser"}
    {"action": "create_file", "path": "notes.txt"}
    {"action": "delete_file", "path": "notes.txt"}
    {"action": "unknown"}                       <- when the text is not a command

The accepted action names and their fields are listed in executor/executor.py.
Voice text is never executed as a shell command: only structured actions reach
the executor, and the executor refuses anything else.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

log = logging.getLogger("mindstack")

GUI_DIR = ROOT / "gui" / "mindstack_gui_english" / "mindstack_gui"

YES_WORDS = {"yes", "yeah", "yep", "confirm", "confirmed", "sure", "okay", "ok"}
NO_WORDS = {"no", "nope", "cancel", "stop"}


# --------------------------------------------------------------------------- #
# Loading the modules owned by other team members
# --------------------------------------------------------------------------- #
def load_understand() -> Callable[[str], dict]:
    """Import nlp.intent.understand, or fall back to a placeholder.

    Only a *missing* nlp module is tolerated. If nlp.intent exists but fails
    to import (a missing library inside it, a syntax error), the real error is
    raised so it is not hidden.
    """
    try:
        from nlp.intent import understand  # type: ignore
        return understand
    except ModuleNotFoundError as exc:
        if exc.name not in ("nlp", "nlp.intent"):
            raise
        log.warning("nlp/intent.py was not found. Every command will be 'unknown' "
                    "until the AI model is connected.")

        def _placeholder(text: str) -> dict:
            return {"action": "unknown"}

        return _placeholder


def load_executor() -> Callable[[object], dict]:
    try:
        from executor.executor import execute_command
    except ModuleNotFoundError as exc:
        if exc.name not in ("executor", "executor.executor"):
            raise
        sys.exit("Cannot import 'executor'. The folder must be named 'executor' "
                 "(lower-case) and sit in the project root, not zipped.")
    return execute_command


# --------------------------------------------------------------------------- #
# Turning executor results into a sentence that sounds fine when spoken
# --------------------------------------------------------------------------- #
def speakable(result: dict) -> str:
    msg = str(result.get("message", "")).strip()
    data = result.get("data")
    if isinstance(data, list) and data:
        names = [d.get("name", str(d)) if isinstance(d, dict) else str(d) for d in data[:3]]
        msg += " First items: " + ", ".join(names) + "."
    elif isinstance(data, dict) and "used_percent" in data:
        msg += f" {data['used_percent']} percent."
    elif isinstance(data, str) and len(data) < 60:
        msg += " " + data
    return msg or ("Done." if result.get("success") else "Something went wrong.")


# --------------------------------------------------------------------------- #
# The pipeline: text in, spoken/printed answer out
# --------------------------------------------------------------------------- #
class Pipeline:
    def __init__(
        self,
        understand: Callable[[str], dict],
        execute: Callable[[object], dict],
        say: Callable[[str], None],
        confirm: Callable[[str], bool],
        allow_json: bool = False,
    ):
        self.understand = understand
        self.execute = execute
        self.say = say
        self.confirm = confirm
        self.allow_json = allow_json  # typed modes only: paste a raw action for debugging

    def _to_action(self, text: str) -> Optional[dict]:
        if self.allow_json and text.lstrip().startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                self.say(f"That is not valid JSON: {exc.msg}")
                return None
        try:
            action = self.understand(text)
        except Exception as exc:  # the AI model must never crash the app
            log.exception("nlp.intent.understand failed")
            self.say(f"Sorry, I had a problem understanding that: {exc}")
            return None
        if not isinstance(action, dict) or action.get("action") in (None, "", "unknown"):
            self.say("Sorry, I did not understand that command.")
            return None
        return action

    @staticmethod
    def describe(action: dict) -> str:
        name = str(action.get("action", "")).replace("_", " ")
        parts = [str(action[k]) for k in
                 ("target", "path", "source", "destination", "new_name", "folder")
                 if action.get(k)]
        return " ".join([name] + parts).strip()

    def run(self, text: str) -> Optional[dict]:
        action = self._to_action(text)
        if action is None:
            return None
        log.info("action: %s", action)

        result = self.execute(action)

        if result.get("error") == "confirmation_required":
            if self.confirm(self.describe(action)):
                # Repeat the exact same action, now confirmed by the user.
                # Approval must be passed as the keyword argument: the executor
                # deletes any "confirmed" key found inside the action dict.
                result = self.execute(action, confirmed=True)
            else:
                self.say("Command cancelled.")
                return {"success": False, "error": "cancelled", "message": "Command cancelled."}

        self.say(speakable(result))
        return result


# --------------------------------------------------------------------------- #
# Input / output helpers
# --------------------------------------------------------------------------- #
def make_say(use_tts: bool) -> Callable[[str], None]:
    speak = None
    if use_tts:
        try:
            from tts.tts import speak as _speak
            speak = _speak
        except Exception as exc:
            log.warning("Text-to-speech is unavailable (%s). Printing answers only.", exc)

    def say(text: str) -> None:
        print(f"MindStack: {text}")
        if speak is not None:
            if speak(text) is False:
                log.warning("tts.speak reported a failure.")

    return say


def make_listen(seconds: int) -> Optional[Callable[[], str]]:
    try:
        from stt.speech_to_text import listen_and_transcribe
    except Exception as exc:  # no ffmpeg, no whisper, no PortAudio ...
        log.error("Speech-to-text is unavailable: %s", exc)
        return None
    return lambda: listen_and_transcribe(seconds=seconds)


def ask_yes_no_typed(description: str) -> bool:
    try:
        answer = input(f"Confirm '{description}'? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in {"y", "yes"}


def make_confirm(say, listen: Optional[Callable[[], str]]) -> Callable[[str], bool]:
    """Ask by voice when a microphone is available, otherwise by keyboard."""

    def confirm(description: str) -> bool:
        say(f"This needs confirmation: {description}. Say yes or no.")
        if listen is not None:
            try:
                words = set(listen().lower().replace(".", " ").replace(",", " ").split())
            except Exception as exc:
                log.warning("Could not listen for the answer (%s).", exc)
                words = set()
            if words & NO_WORDS:
                return False
            if words & YES_WORDS:
                return True
            print("I did not catch a clear yes or no.")
        return ask_yes_no_typed(description)

    return confirm


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def interactive_loop(pipeline: Pipeline, listen: Optional[Callable[[], str]], once: bool) -> int:
    if listen is not None:
        print("Press Enter to speak, or type a command. Type 'q' to quit.")
    else:
        print("Type a command. Type 'q' to quit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line.lower() in {"q", "quit", "exit"}:
            return 0

        if line:
            text = line
        elif listen is not None:
            try:
                print("Listening...")
                text = listen()
            except Exception as exc:
                pipeline.say(f"Microphone or speech error: {exc}")
                continue
            if not text:
                pipeline.say("I did not hear anything. Please try again.")
                continue
            print(f"Heard: {text}")
        else:
            continue

        pipeline.run(text)
        if once:
            return 0


def run_gui() -> int:
    """Start the PySide6 GUI wired to the real backend (falls back to the mock)."""
    if not (GUI_DIR / "main.py").is_file():
        sys.exit(f"GUI not found at {GUI_DIR}")
    sys.path.insert(0, str(GUI_DIR))

    spec = importlib.util.spec_from_file_location("mindstack_gui_main", GUI_DIR / "main.py")
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)

    try:
        from app.real_backend import RealBackend
        gui.create_backend = lambda: RealBackend()
    except ModuleNotFoundError as exc:
        if exc.name not in ("app.real_backend", "app"):
            raise
        log.warning("gui/.../app/real_backend.py is missing (still zipped?). "
                    "Starting with MockBackend.")
    return gui.main()


# --------------------------------------------------------------------------- #
def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MindStack: Voice-Enhanced Linux")
    p.add_argument("command", nargs="?", help="run this one typed command and exit")
    p.add_argument("--text", action="store_true", help="typed mode (no microphone)")
    p.add_argument("--gui", action="store_true", help="start the graphical interface")
    p.add_argument("--no-tts", action="store_true", help="do not speak, only print")
    p.add_argument("--once", action="store_true", help="handle one command, then exit")
    p.add_argument("--seconds", type=int, default=5, help="recording length (default 5)")
    p.add_argument("-v", "--verbose", action="store_true", help="show debug logging")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.gui:
        return run_gui()

    typed = args.text or args.command is not None
    listen = None if typed else make_listen(args.seconds)
    if not typed and listen is None:
        log.error("No microphone pipeline available. Falling back to typed mode.")
        typed = True

    say = make_say(not args.no_tts)
    pipeline = Pipeline(
        understand=load_understand(),
        execute=load_executor(),
        say=say,
        confirm=make_confirm(say, listen),
        allow_json=typed,
    )

    if args.command is not None:
        result = pipeline.run(args.command)
        return 0 if result and result.get("success") else 1
    return interactive_loop(pipeline, listen, args.once)


if __name__ == "__main__":
    sys.exit(main())

