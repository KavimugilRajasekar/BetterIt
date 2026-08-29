"""The top-level application: wires the hotkey, the floating window, the LLM
worker, and the clipboard paste-back into a single end-to-end loop.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import clipboard, llm
from .hotkey import GlobalHotkey
from .window import FloatingWindow, load_fonts


# --- LLM worker thread ------------------------------------------------------

class GrammarWorker(QObject):
    """Runs `llm.transform_text` off the GUI thread."""

    finished = Signal(str)  # the transformed text
    failed = Signal(str)    # an error message

    def __init__(self, text: str, prompt: str = "") -> None:
        super().__init__(None)  # Worker is created without parent to allow thread move
        self._text = text
        self._prompt = prompt

    @Slot()
    def run(self) -> None:
        try:
            transformed = llm.transform_text(self._text, prompt=self._prompt)
        except llm.GrammarError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # safety net
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.finished.emit(transformed)


# --- Application ------------------------------------------------------------

class AIWriterApp(QObject):
    """Owns the QApplication, the floating window, and the hotkey listener."""

    def __init__(self) -> None:
        super().__init__()
        # Load .env before anything tries to read API keys.
        load_dotenv()

        if not os.environ.get("OPEN_ROUTER"):
            print(
                "OPEN_ROUTER is not set. Add your OpenRouter API key to .env.",
                file=sys.stderr,
            )

        self._qt = QApplication(sys.argv)
        self._qt.setQuitOnLastWindowClosed(False)  # tray-only lifecycle

        # Load bundled typography cleanly on start
        load_fonts()

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
        self._tray.setToolTip("BetterIt AI Writer")

        menu = QMenu()
        quit_action = QAction("Quit BetterIt", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _connect_signals(self) -> None:
        # Hotkey fires in a worker thread; since AIWriterApp is a QObject,
        # Qt queues the signal onto the GUI thread automatically.
        self._hotkey.triggered.connect(self._on_hotkey, Qt.ConnectionType.QueuedConnection)
        # Window asks us to do work with text and prompt
        self._window.correct_requested.connect(self._on_correct_requested)
        self._window.replace_requested.connect(self._on_replace_requested)
        self._window.closed.connect(self._on_window_closed)

    # -- Slots -------------------------------------------------------------

    @Slot()
    def _on_hotkey(self) -> None:
        """User pressed Ctrl+Space somewhere. Grab the selection and show the UI."""
        # Capture the source window *before* we touch the clipboard, so the
        # paste-back step knows where to land.
        self._source_hwnd = clipboard.get_foreground_hwnd()
        try:
            selected = clipboard.read_selected()
        except Exception as exc:
            msg = f"Could not read selection: {exc}"
            self._window.show_error(msg)
            return

        if not selected or not selected.strip():
            # Nothing was selected — silently do nothing.
            return

        self._window.show_for_text(selected)

    @Slot(str, str)
    def _on_correct_requested(self, text: str, prompt: str = "") -> None:
        """User clicked Polish / Transform. Run the LLM in a worker thread."""
        # Tear down any previous worker safely.
        self._cleanup_worker()

        thread = QThread()
        worker = GrammarWorker(text, prompt=prompt)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_llm_finished, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(self._on_llm_failed, Qt.ConnectionType.QueuedConnection)

        # Clean up thread and worker on finish
        worker.finished.connect(thread.quit, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(thread.quit, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._worker_thread = thread
        thread.start()

    @Slot(str)
    def _on_llm_finished(self, corrected: str) -> None:
        self._window.show_improved(corrected)

    @Slot(str)
    def _on_llm_failed(self, message: str) -> None:
        self._window.show_error(message)

    @Slot(str)
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
        pass

    # -- Helpers -----------------------------------------------------------

    def _cleanup_worker(self) -> None:
        if self._worker_thread is not None:
            try:
                if self._worker_thread.isRunning():
                    self._worker_thread.quit()
                    self._worker_thread.wait(1000)
            except Exception:
                pass
            self._worker_thread = None
        self._worker = None

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
