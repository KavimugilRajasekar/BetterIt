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
from .settings import QuickReplaceToast, TransientPencilLoader
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

        from .tag_store import TagStore
        self._store = TagStore()
        if not self._store.get_active_api_key():
            print(
                "OpenRouter API key is not configured yet. Press Ctrl+Space with no text to configure it in Settings.",
                file=sys.stderr,
            )

        self._qt = QApplication(sys.argv)
        self._qt.setQuitOnLastWindowClosed(False)  # tray-only lifecycle

        # Load bundled typography cleanly on start
        load_fonts()

        self._window = FloatingWindow(self._store)
        self._hotkey = GlobalHotkey(os.environ.get("HOTKEY", "ctrl+space"))
        self._worker: Optional[GrammarWorker] = None
        self._worker_thread: Optional[QThread] = None
        self._source_hwnd: int = 0
        # Quick-Replace worker (separate from the normal FloatingWindow worker)
        self._qr_worker: Optional[GrammarWorker] = None
        self._qr_thread: Optional[QThread] = None
        self._qr_hwnd: int = 0
        # Pause quick-replace / normal hotkey while Settings window is visible
        self._settings_open: bool = False
        self._active_qr_loader: Optional[QWidget] = None

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
        # Track Settings open/close so we can pause the hotkey logic
        self._window.settings_opened.connect(self._on_settings_opened)
        self._window.settings_closed.connect(self._on_settings_closed)

    # -- Slots -------------------------------------------------------------

    @Slot()
    def _on_settings_opened(self) -> None:
        self._settings_open = True

    @Slot()
    def _on_settings_closed(self) -> None:
        self._settings_open = False

    @Slot()
    def _on_hotkey(self) -> None:
        """User pressed Ctrl+Space somewhere. Grab the selection and show the UI."""
        # While Settings is open, ignore the hotkey completely.
        if self._settings_open:
            return

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
            # Nothing was selected — open Settings panel directly instead of floating window
            self._window.open_settings("Edit Tag", show_return=False)
            return

        # --- Quick Replace mode ---
        if self._store.get_config("quick_replace", False):
            self._qr_hwnd = self._source_hwnd
            self._start_quick_replace(selected)
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

    def _cleanup_qr_worker(self) -> None:
        if self._qr_thread is not None:
            try:
                if self._qr_thread.isRunning():
                    self._qr_thread.quit()
                    self._qr_thread.wait(1000)
            except Exception:
                pass
            self._qr_thread = None
        self._qr_worker = None

    def _start_quick_replace(self, text: str) -> None:
        """Launch an LLM transform in the background and auto-paste the result."""
        self._cleanup_qr_worker()

        # --- Loader Logic ---
        # 1. Check if the minimized BallWidget is visible
        ball_visible = False
        sw = getattr(self._window, "_settings_window", None)
        if sw and getattr(sw, "_ball", None) and sw._ball.isVisible():
            ball_visible = True

        if ball_visible:
            # Proxy loading state to the ball
            self._window.set_settings_ball_loading(True)
            self._active_qr_loader = sw._ball
        else:
            # Show transient loader at bottom-center
            loader = TransientPencilLoader()
            loader.set_loading(True)
            self._active_qr_loader = loader

        # Get the active tag's prompt so QR uses same polish rules.
        try:
            from . import llm as _llm
            prompt = _llm._get_active_prompt()
        except Exception:
            prompt = ""

        thread = QThread()
        worker = GrammarWorker(text, prompt=prompt)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_qr_finished, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(self._on_qr_failed, Qt.ConnectionType.QueuedConnection)

        worker.finished.connect(thread.quit, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(thread.quit, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._qr_worker = worker
        self._qr_thread = thread
        thread.start()

    @Slot(str)
    def _on_qr_finished(self, corrected: str) -> None:
        """Quick Replace succeeded — paste result back silently."""
        # Reset loader
        if self._active_qr_loader:
            if isinstance(self._active_qr_loader, TransientPencilLoader):
                self._active_qr_loader.set_loading(False)
                self._active_qr_loader.hide()
            else:
                self._window.set_settings_ball_loading(False)
            self._active_qr_loader = None

        # Detect obviously garbled / unusable output (empty, or contains 'Jumple'
        # which indicates the LLM couldn't handle the text).
        stripped = corrected.strip()
        if not stripped or "jumple" in stripped.lower():
            self._show_qr_error("Operation cannot be done because the AI returned an unusable response.")
            return
        QTimer.singleShot(80, lambda: self._do_qr_paste(corrected))

    @Slot(str)
    def _on_qr_failed(self, message: str) -> None:
        """Quick Replace LLM call failed — show a toast instead of the full window."""
        self._show_qr_error(message)

    def _do_qr_paste(self, corrected: str) -> None:
        try:
            clipboard.focus_window(self._qr_hwnd)
            clipboard.paste_back(corrected)
        except Exception as exc:
            self._show_qr_error(f"Could not paste: {exc}")

    def _show_qr_error(self, message: str) -> None:
        """Show error in the active loader, or fallback to toast."""
        if self._active_qr_loader:
            self._active_qr_loader.set_error(message)
            # If it's a transient loader, it's already visible.
            # If it's the ball, it's already visible.
            # We might want to hide it after a few seconds.
            QTimer.singleShot(3000, self._clear_qr_loader)
            return

        # Fallback to the old toast logic if no loader is active
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        toast_host = self._window
        # If the floating window is hidden, show it at screen centre first.
        if not toast_host.isVisible():
            screen = self._qt.primaryScreen().availableGeometry()
            toast_host.move(
                screen.center().x() - toast_host.width() // 2,
                screen.center().y() - toast_host.height() // 2,
            )
            toast_host.show()
        QuickReplaceToast.show_error(toast_host, message)

    def _clear_qr_loader(self) -> None:
        """Reset the active QR loader to IDLE and hide if transient."""
        if self._active_qr_loader:
            if isinstance(self._active_qr_loader, TransientPencilLoader):
                self._active_qr_loader.set_error(None)
                self._active_qr_loader.hide()
            else:
                self._window.set_settings_ball_loading(False)
            self._active_qr_loader = None

    def _quit(self) -> None:
        self._cleanup_worker()
        self._cleanup_qr_worker()
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
