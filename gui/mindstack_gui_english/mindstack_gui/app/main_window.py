"""Main window: sidebar navigation + stacked pages + status bar + tray icon."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, APP_SUBTITLE
from .controller import Controller
from .dialogs.about_dialog import AboutDialog
from .dialogs.confirm_dialog import ConfirmDialog
from .dialogs.mic_test_dialog import MicTestDialog
from .icons import make_app_icon
from .models import SettingsStore
from .pages.commands_page import CommandsPage
from .pages.home_page import HomePage
from .pages.log_page import LogPage
from .pages.settings_page import SettingsPage
from .state import STATE_COLORS, STATE_INFO, AppState
from .theme import apply_theme

PAGES = ("Home", "Command log", "Commands", "Settings")


class MainWindow(QMainWindow):
    def __init__(self, controller: Controller, settings: SettingsStore):
        super().__init__()
        self.ctl = controller
        self.settings = settings
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE}")
        self.setWindowIcon(make_app_icon())
        self.resize(1120, 720)
        self.setMinimumSize(920, 620)

        central = QWidget()
        self.setCentralWidget(central)
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        row.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.home = HomePage(self.ctl)
        self.log = LogPage(self.ctl, notify=self.notify)
        self.commands = CommandsPage()
        self.settings_page = SettingsPage(self.settings, self.open_mic_test)
        for page in (self.home, self.log, self.commands, self.settings_page):
            self.stack.addWidget(page)
        row.addWidget(self.stack, 1)

        self.commands.try_phrase.connect(self._try_phrase)
        self.statusBar().showMessage("Ready")

        self._wire_controller()
        self._wire_shortcuts()
        self._build_tray()
        self._on_state(self.ctl.state)
        self._go(0)

    # ------------------------------------------------------------- building
    def _build_sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(220)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(14, 22, 14, 16)
        lay.setSpacing(4)

        brand = QLabel(APP_NAME)
        brand.setObjectName("Brand")
        sub = QLabel(APP_SUBTITLE)
        sub.setObjectName("BrandSub")
        lay.addWidget(brand)
        lay.addWidget(sub)
        lay.addSpacing(22)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for i, name in enumerate(PAGES):
            btn = QPushButton(f"{name}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{name}  (Ctrl+{i + 1})")
            self.nav_group.addButton(btn, i)
            lay.addWidget(btn)
        self.nav_group.idClicked.connect(self._go)

        lay.addStretch(1)

        chip = QFrame()
        chip.setObjectName("StatusChip")
        chip_l = QHBoxLayout(chip)
        chip_l.setContentsMargins(12, 9, 12, 9)
        self.chip_dot = QLabel("●")
        self.chip_text = QLabel()
        chip_l.addWidget(self.chip_dot)
        chip_l.addWidget(self.chip_text, 1)
        lay.addWidget(chip)
        lay.addSpacing(6)

        about = QPushButton("About")
        about.clicked.connect(lambda: AboutDialog(self).exec())
        lay.addWidget(about)
        return side

    def _wire_controller(self) -> None:
        self.ctl.state_changed.connect(self._on_state)
        self.ctl.confirmation_requested.connect(self._ask_confirmation)
        self.ctl.error_occurred.connect(self._show_error)
        self.settings.changed.connect(self._on_setting_changed)

    def _wire_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.ctl.toggle_listening)
        for i in range(len(PAGES)):
            QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self,
                      activated=lambda i=i: self._go(i))

    def _build_tray(self) -> None:
        self.tray: QSystemTrayIcon | None = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        menu = QMenu(self)
        show = QAction("Show window", self, triggered=self._show_window)
        toggle = QAction("Start / stop listening", self,
                         triggered=self.ctl.toggle_listening)
        quit_ = QAction("Quit", self, triggered=QApplication.quit)
        for a in (show, toggle):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(quit_)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip(APP_NAME)
        self.tray.activated.connect(
            lambda reason: self._show_window()
            if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    # --------------------------------------------------------------- actions
    def _go(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.nav_group.button(index).setChecked(True)

    def notify(self, text: str) -> None:
        self.statusBar().showMessage(text, 6000)

    def open_mic_test(self) -> None:
        MicTestDialog(self.ctl, self).exec()

    def _try_phrase(self, phrase: str) -> None:
        self._go(0)
        self.ctl.submit_text(phrase)

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # --------------------------------------------------------------- slots
    def _on_state(self, state: AppState) -> None:
        title = STATE_INFO[state][0].rstrip("…")
        self.chip_text.setText(title)
        self.chip_dot.setStyleSheet(
            f"color: {STATE_COLORS[state]}; background: transparent; font-size: 14px;")
        self.statusBar().showMessage(STATE_INFO[state][1])

    def _ask_confirmation(self, command_text: str) -> None:
        dlg = ConfirmDialog(command_text, self)
        self.ctl.answer_confirmation(dlg.exec() == ConfirmDialog.Accepted)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, APP_NAME, message)

    def _on_setting_changed(self, key: str, value) -> None:
        if key == "theme":
            apply_theme(QApplication.instance(), value)

    def closeEvent(self, event) -> None:
        self.ctl.shutdown()
        if self.tray:
            self.tray.hide()
        super().closeEvent(event)
