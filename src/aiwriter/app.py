"""The top-level application: wires the hotkey, the floating window, the LLM
worker, and the clipboard paste-back into a single end-to-end loop.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import clipboard, llm
from .hotkey import GlobalHotkey
from .window import FloatingWindow


# --- LLM worker thread ------------------------------------------------------

class GrammarWorker(QObject):
    """Runs `llm.correct_grammar` off the GUI thread."""

    finished = Signal(str)  # the corrected text
    failed = Signal(str)    # an error message

    def __init__(self, text: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._text = text

    def run(self) -> None:
        try:
            corrected = llm.correct_grammar(self._text)
        except llm.GrammarError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # last-ditch safety net
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished.emit(corrected)


# --- Application ------------------------------------------------------------

class AIWriterApp:
    """Owns the QApplication, the floating window, and the hotkey listener."""

    def __init__(self) -> None:
        # Load .env before anything tries to read OPENAI_API_KEY.
        load_dotenv()

        if not os.environ.get("OPEN_ROUTER"):
            print(
                "OPEN_ROUTER is not set. Add your OpenRouter API key to .env.",
                file=sys.stderr,
            )

        self._qt = QApplication(sys.argv)
        self._qt.setQuitOnLastWindowClosed(False)  # tray-only lifecycle

        self._window = FloatingWindow()
        self._hotkey = GlobalHotkey(os.environ.get("HOTKEY", "ctrl+space"))
        self._worker: Optional[GrammarWorker] = None
        self._worker_thread: Optional[QThread] = None
        self._source_hwnd: int = 0

        self._setup_tray()
        self._connect_signals()
        self._hotkey.start()

    # -- Wiring ------------------------------------------------------------

    def _setup_tray(self) -> None:
        icon = self._qt.style().standardIcon(
            self._qt.style().StandardPixmap.SP_DialogApplyButton
        )
        self._tray = QSystemTrayIcon(icon, self._qt)
        self._tray.setToolTip("AI Writing Assistant")

        menu = QMenu()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _connect_signals(self) -> None:
        # Hotkey fires in a worker thread; the signal marshals to the GUI thread.
        self._hotkey.triggered.connect(self._on_hotkey)
        # Window asks us to do work.
        self._window.correct_requested.connect(self._on_correct_requested)
        self._window.replace_requested.connect(self._on_replace_requested)
        self._window.closed.connect(self._on_window_closed)

    # -- Slots -------------------------------------------------------------

    def _on_hotkey(self) -> None:
        """User pressed Ctrl+Space somewhere. Grab the selection and show the UI."""
        # Capture the source window *before* we touch the clipboard, so the
        # paste-back step knows where to land.
        self._source_hwnd = clipboard.get_foreground_hwnd()
        try:
            selected = clipboard.read_selected()
        except Exception as exc:
            self._window.show_error(f"Could not read selection: {exc}")
            return

        if not selected or not selected.strip():
            # Nothing was selected — silently do nothing. Don't even flash the
            # window; that would be annoying if the user pressed the hotkey
            # by accident.
            return

        self._window.show_for_text(selected)

    def _on_correct_requested(self, text: str) -> None:
        """User clicked Correct Grammar. Run the LLM in a worker thread."""
        # Tear down any previous worker.
        self._cleanup_worker()

        thread = QThread(self._qt)
        worker = GrammarWorker(text)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_llm_finished)
        worker.failed.connect(self._on_llm_failed)

        # Once the worker is done, quit the thread.
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._worker_thread = thread
        thread.start()

    def _on_llm_finished(self, corrected: str) -> None:
        self._window.show_improved(corrected)

    def _on_llm_failed(self, message: str) -> None:
        self._window.show_error(message)

    def _on_replace_requested(self, corrected: str) -> None:
        """User clicked Replace. Paste into the source app."""
        # Hide first so the source window comes to the front cleanly.
        self._window.hide()
        # Tiny delay so the OS focuses the underlying app before we send keys.
        QTimer.singleShot(50, lambda: self._do_paste(corrected))

    def _do_paste(self, corrected: str) -> None:
        try:
            clipboard.focus_window(self._source_hwnd)
            clipboard.paste_back(corrected)
        except Exception as exc:
            # Re-show the window with the error so the user knows.
            self._window.show_error(f"Could not paste: {exc}")

    def _on_window_closed(self) -> None:
        # Nothing to do; placeholder for future "remember last position" logic.
        pass

    # -- Helpers -----------------------------------------------------------

    def _cleanup_worker(self) -> None:
        if self._worker_thread is not None:
            try:
                if self._worker_thread.isRunning():
                    self._worker_thread.quit()
                    self._worker_thread.wait(2000)
            except Exception:
                pass
        self._worker = None
        self._worker_thread = None

    def _quit(self) -> None:
        self._cleanup_worker()
        self._hotkey.stop()
        self._qt.quit()

    # -- Entry point -------------------------------------------------------

    def run(self) -> int:
        return self._qt.exec()


def main() -> int:
    app = AIWriterApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
