#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QGuiApplication, QFont
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
import os
import signal

LOCK_FILE = "/tmp/bigclock.pid"

def cleanup():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def handle_existing_instance():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())

            # Check if process is alive
            os.kill(old_pid, 0)

            # Kill it
            os.kill(old_pid, signal.SIGTERM)
            print("Closed existing instance")
            sys.exit(0)

        except (ValueError, ProcessLookupError, PermissionError):
            pass  # stale PID, ignore

    # Write current PID
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

class ClockOverlay(QWidget):
    def __init__(self, screen):
        handle_existing_instance()
        super().__init__()
        self._target_screen = screen

        # Create label FIRST
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: white;")

        font = QFont("DejaVu Sans", 96, QFont.Weight.Bold)
        self.label.setFont(font)

        # Window setup AFTER
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        print(f"target screen: {screen.name()}")
        self._apply_target_screen()
        # On Wayland, the compositor may ignore the initial placement hint until the
        # native window exists. Re-apply once the window handle is created.
        QTimer.singleShot(0, self._apply_target_screen)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 160);")

        # Timer
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        self.update_time()

    def update_time(self):
        now = datetime.now()
        text = now.strftime("%A, %B %d %Y\n%I:%M %p")
        self.label.setText(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        self.close()

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())

    def focusOutEvent(self, event):
        self.close()

    def closeEvent(self, event):
        QApplication.quit()

    def _apply_target_screen(self):
        screen = self._target_screen
        if screen is None:
            return

        # Provide multiple hints; different backends honor different ones.
        self.setScreen(screen)
        self.setGeometry(screen.geometry())

        handle = self.windowHandle()
        if handle is not None:
            handle.setScreen(screen)

        self.showFullScreen()

def rightmost_screen():
    screens = QGuiApplication.screens()
    if not screens:
        return None
    return max(screens, key=lambda s: s.geometry().x() + s.geometry().width())

def dump_screens(tag=""):
    print(f"\n--- QGuiApplication.screens() {tag} ---")
    screens = QGuiApplication.screens()
    for i, s in enumerate(screens):
        g = s.geometry()
        ag = s.availableGeometry()
        print(
            f"[{i}] name={s.name()} "
            f"geo=({g.x()},{g.y()},{g.width()}x{g.height()}) "
            f"avail=({ag.x()},{ag.y()},{ag.width()}x{ag.height()}) "
            f"dpr={s.devicePixelRatio()}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(cleanup)

    # print(f"Qt platform: {QGuiApplication.platformName()}")
    # dump_screens("at start")
    # _screen_dump_timer = QTimer()
    # _screen_dump_timer.timeout.connect(lambda: dump_screens("tick"))
    # _screen_dump_timer.start(1000)
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        screen = app.primaryScreen()

    overlay = ClockOverlay(screen)

    sys.exit(app.exec())