#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
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
    def __init__(self):
        handle_existing_instance()
        super().__init__()

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

        self.showFullScreen()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(cleanup)
    overlay = ClockOverlay()
    overlay.show()
    sys.exit(app.exec())