"""MindStack GUI entry point.

Run:   python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from app import APP_NAME
from app.backend import MockBackend
from app.controller import Controller
from app.icons import make_app_icon
from app.main_window import MainWindow
from app.models import SettingsStore
from app.theme import apply_theme, setup_fonts


def create_backend():
    """Return the backend the GUI talks to.

    TODO (team integration): replace MockBackend with the real implementation
    that wires Vosk / SpeechRecognition + command parser + subprocess + pyttsx3.
    It only has to follow the BaseBackend contract in app/backend.py.
    """
    return MockBackend()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("MindStack")
    app.setStyle("Fusion")
    app.setWindowIcon(make_app_icon())
    setup_fonts(app)

    settings = SettingsStore()
    apply_theme(app, settings.get("theme"))

    controller = Controller(create_backend(), settings)
    window = MainWindow(controller, settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
