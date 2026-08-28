"""
BetterIt - UI Only Test Launcher

Runs only the FloatingWindow UI.
No AI worker.
No hotkey listener.
No clipboard integration.
No background threads.

Use this file to test the visual interface independently.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

# Allow imports from ./src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Import your existing BetterIt UI
# ---------------------------------------------------------------------------

from aiwriter.window import FloatingWindow


# ---------------------------------------------------------------------------
# UI-only test application
# ---------------------------------------------------------------------------

class UITestWindow(QWidget):
    """
    Small development launcher used only for testing FloatingWindow.

    This does NOT start BetterIt's AI worker or any background service.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("BetterIt - UI Test")
        self.setFixedSize(460, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("BetterIt UI Test")
        title.setStyleSheet("""
            QLabel {
                font-family: "Comfortaa";
                font-size: 20px;
                font-weight: 700;
            }
        """)

        description = QLabel(
            "This launcher tests only the floating BetterIt window."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                font-family: "Comfortaa";
                font-size: 13px;
            }
        """)

        show_button = QPushButton("Open Better It")
        show_button.setFixedHeight(44)
        show_button.setStyleSheet("""
            QPushButton {
                font-family: "Comfortaa";
                font-size: 13px;
                font-weight: 700;
                border-radius: 22px;
                padding: 8px 18px;
                background-color: #2e7d32;
                color: white;
                border: 2px solid #0a0a0a;
            }

            QPushButton:hover {
                background-color: #388e3c;
            }

            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(show_button)

        # ---------------------------------------------------------------
        # Create ONLY the floating UI
        # ---------------------------------------------------------------

        self.floating = FloatingWindow()

        # We deliberately don't connect the AI signals to a worker.
        #
        # Instead, the test launcher simulates the UI state changes.
        self.floating.correct_requested.connect(
            self._simulate_correction
        )

        self.floating.replace_requested.connect(
            self._replacement_received
        )

        show_button.clicked.connect(self._open_test_ui)

    # ------------------------------------------------------------------
    # Open floating window
    # ------------------------------------------------------------------

    def _open_test_ui(self) -> None:
        test_text = (
            "This is a test sentence with some bad grammar "
            "and spelling mistake."
        )

        self.floating.show_for_text(test_text)

    # ------------------------------------------------------------------
    # Simulated AI response
    # ------------------------------------------------------------------

    def _simulate_correction(self, original: str) -> None:
        """
        Simulates the AI without creating another thread.

        This exists ONLY so the visual states of the UI can be tested.
        """

        self.floating.show_loading()

        corrected = (
            "This is a test sentence with improved grammar "
            "and corrected spelling."
        )

        # Simulate an AI delay.
        QTimer.singleShot(
            1200,
            lambda: self.floating.show_improved(corrected)
        )

    # ------------------------------------------------------------------
    # Replace button
    # ------------------------------------------------------------------

    def _replacement_received(self, text: str) -> None:
        """
        Called when Replace is clicked.

        For UI testing we simply print the resulting text.
        """

        print()
        print("=" * 60)
        print("REPLACEMENT REQUESTED")
        print("=" * 60)
        print(text)
        print("=" * 60)
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    app = QApplication(sys.argv)

    # ------------------------------------------------------------------
    # Load bundled fonts BEFORE creating widgets
    # ------------------------------------------------------------------

    from PySide6.QtGui import QFontDatabase

    fonts_dir = ROOT_DIR / "fonts"

    comfortaa = (
        fonts_dir
        / "Comfortaa"
        / "Comfortaa-VariableFont_wght.ttf"
    )

    playwrite = (
        fonts_dir
        / "Playwrite_US_Modern"
        / "PlaywriteUSModern.ttf"
    )

    # Fallback to static fonts if necessary.
    if not comfortaa.exists():
        comfortaa = (
            fonts_dir
            / "Comfortaa"
            / "static"
            / "Comfortaa-Regular.ttf"
        )

    if not playwrite.exists():
        playwrite = (
            fonts_dir
            / "Playwrite_US_Modern"
            / "static"
            / "PlaywriteUSModern-Regular.ttf"
        )

    if comfortaa.exists():
        font_id = QFontDatabase.addApplicationFont(
            str(comfortaa)
        )

        if font_id >= 0:
            print(f"[BetterIt] Comfortaa loaded: {comfortaa}")
        else:
            print("[BetterIt] Failed to load Comfortaa")

    else:
        print("[BetterIt] Comfortaa font not found")

    if playwrite.exists():
        font_id = QFontDatabase.addApplicationFont(
            str(playwrite)
        )

        if font_id >= 0:
            print(f"[BetterIt] Playwrite US Modern loaded: {playwrite}")
        else:
            print("[BetterIt] Failed to load Playwrite US Modern")

    else:
        print("[BetterIt] Playwrite US Modern font not found")

    # ------------------------------------------------------------------
    # Start UI test
    # ------------------------------------------------------------------

    test_window = UITestWindow()
    test_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()