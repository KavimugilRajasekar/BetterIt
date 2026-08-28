"""Global hotkey listener. Runs the `keyboard` library in a daemon thread and
relays triggers back to the Qt main thread via a signal.
"""
from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal


class GlobalHotkey(QObject):
    """Listen for a global hotkey combination and emit `triggered` on press.

    The `keyboard` library's blocking listener runs in a daemon thread; we
    forward each trigger to the GUI thread through a Qt signal, which keeps
    all widget manipulation safely on the main thread.
    """

    triggered = Signal()

    def __init__(self, hotkey: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._registered = False
        self._listener = None  # type: ignore[var-annotated]

    def start(self) -> None:
        """Begin listening. Safe to call once."""
        if self._registered:
            return
        # Defer the import so a missing `keyboard` install doesn't break the
        # rest of the app at module-load time.
        import keyboard  # type: ignore[import-untyped]

        # The callback runs in `keyboard`'s own thread.
        keyboard.add_hotkey(
            self._hotkey,
            self._on_pressed,
            suppress=False,
            trigger_on_release=False,
        )
        self._registered = True

    def stop(self) -> None:
        """Stop listening. Idempotent."""
        if not self._registered:
            return
        try:
            import keyboard  # type: ignore[import-untyped]

            keyboard.remove_hotkey(self._hotkey)
        except Exception:
            # Removing the hotkey can race with shutdown; ignore.
            pass
        self._registered = False

    def _on_pressed(self) -> None:
        # We're on a non-GUI thread here. Emit the signal; Qt queues it
        # onto the thread that owns this QObject (the main thread).
        self.triggered.emit()


def install_daemon(hotkey: str, callback: Callable[[], None]) -> threading.Thread:
    """Convenience: run a `keyboard.wait()` loop in a daemon thread.

    Provided for callers that prefer a thread-based approach over the
    QObject signal. The given `callback` runs in the daemon thread, so
    it is responsible for marshalling onto the GUI thread itself.
    """
    def _run() -> None:
        import keyboard  # type: ignore[import-untyped]

        keyboard.add_hotkey(hotkey, callback, suppress=False)
        keyboard.wait()

    thread = threading.Thread(target=_run, name="aiwriter-hotkey", daemon=True)
    thread.start()
    return thread
