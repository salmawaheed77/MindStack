"""Application states shown by the GUI."""

from enum import Enum


class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


# title, hint  (shown on the Home page under the status orb)
STATE_INFO = {
    AppState.IDLE: (
        "Idle",
        "Press the microphone button or Ctrl+L to start listening.",
    ),
    AppState.LISTENING: (
        "Listening…",
        "Speak a command, for example \"open browser\".",
    ),
    AppState.PROCESSING: (
        "Processing…",
        "Understanding and validating the command.",
    ),
    AppState.SPEAKING: (
        "Speaking…",
        "Reading the result aloud.",
    ),
    AppState.ERROR: (
        "Error",
        "Something went wrong. Check the microphone and try again.",
    ),
}

STATE_COLORS = {
    AppState.IDLE: "#8B95A8",
    AppState.LISTENING: "#2ECC8F",
    AppState.PROCESSING: "#F5B942",
    AppState.SPEAKING: "#4F8CFF",
    AppState.ERROR: "#FF5C6C",
}
