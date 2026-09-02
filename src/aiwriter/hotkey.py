"""Global hotkey listener. Runs the `keyboard` library in a daemon thread and
relays triggers back to the Qt main thread via a signal.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

from PySide6.QtCore import QObject, Signal

# Minimum seconds between two accepted triggers (debounce guard).
_DEBOUNCE_SECONDS = 0.3

# Canonical modifier names (base form, no left/right prefix).
_BASE_MODIFIERS: frozenset[str] = frozenset({"ctrl", "shift", "alt", "windows"})

# Map every variant the keyboard library may report → canonical base name.
_MODIFIER_CANONICAL: dict[str, str] = {
    "ctrl": "ctrl", "left ctrl": "ctrl", "right ctrl": "ctrl",
    "shift": "shift", "left shift": "shift", "right shift": "shift",
    "alt": "alt", "left alt": "alt", "right alt": "alt",
    "windows": "windows", "left windows": "windows", "right windows": "windows",
}

# All variant names the library may surface (used for is_pressed checks).
_ALL_MODIFIER_VARIANTS: tuple[str, ...] = tuple(_MODIFIER_CANONICAL.keys())


def _parse_modifiers(hotkey: str) -> frozenset[str]:
    """Return the *canonical* modifier base-names required by *hotkey*.

    ``"ctrl+space"``    → ``frozenset({"ctrl"})``
    ``"ctrl+shift+a"``  → ``frozenset({"ctrl", "shift"})``
    """
    parts = {p.strip().lower() for p in hotkey.split("+")}
    return frozenset(
        _MODIFIER_CANONICAL[p] for p in parts if p in _MODIFIER_CANONICAL
    )


def _extra_modifier_held(required: frozenset[str]) -> bool:
    """Return True if any modifier that is NOT in *required* is currently pressed.

    Checks every left/right variant so that pressing Left-Ctrl is treated the
    same as Ctrl, etc.  This prevents ``ctrl+space`` from firing when the user
    is actually doing ``ctrl+shift+space`` (a common zoom shortcut).
    """
    try:
        import keyboard  # type: ignore[import-untyped]

        for variant, base in _MODIFIER_CANONICAL.items():
            if base not in required and keyboard.is_pressed(variant):
                return True
    except Exception:
        pass  # if the check itself fails, allow the trigger
    return False


class GlobalHotkey(QObject):
    """Listen for a global hotkey combination and emit `triggered` on press.

    The `keyboard` library's blocking listener runs in a daemon thread; we
    forward each trigger to the GUI thread through a Qt signal, which keeps
    all widget manipulation safely on the main thread.

    Extra-modifier guard
    --------------------
    The ``keyboard`` library fires a hotkey callback whenever the required
    keys are down, regardless of *other* keys that may also be held at that
    moment.  This means ``ctrl+space`` would also fire during
    ``ctrl+shift+space``, ``ctrl+alt+space``, etc.  We guard against this by
    checking at callback time that no *extra* modifier is pressed beyond those
    explicitly listed in the configured hotkey.

    Debounce guard
    --------------
    A 300 ms debounce prevents the callback from firing multiple times in
    rapid succession (e.g. when the user holds the combo briefly).
    """

    triggered = Signal()

    def __init__(self, hotkey: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._required_modifiers: frozenset[str] = _parse_modifiers(hotkey)
        self._registered = False
        self._listener = None  # type: ignore[var-annotated]
        self._last_trigger: float = 0.0

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
        """Called by the keyboard library on its own thread when the hotkey fires."""
        # --- Extra-modifier guard ---
        # Reject if any modifier NOT part of our hotkey is held down.
        # Uses normalised left/right variants so pressing Left-Ctrl still
        # matches "ctrl" and isn't falsely blocked.
        if _extra_modifier_held(self._required_modifiers):
            return

        # --- Debounce guard ---
        now = time.monotonic()
        if now - self._last_trigger < _DEBOUNCE_SECONDS:
            return
        self._last_trigger = now

        # We're on a non-GUI thread here. Emit the signal; Qt queues it
        # onto the thread that owns this QObject (the main thread).
        self.triggered.emit()


def install_daemon(hotkey: str, callback: Callable[[], None]) -> threading.Thread:
    """Convenience: run a `keyboard.wait()` loop in a daemon thread.

    Provided for callers that prefer a thread-based approach over the
    QObject signal. The given `callback` runs in the daemon thread, so
    it is responsible for marshalling onto the GUI thread itself.

    Applies the same extra-modifier and debounce guards as :class:`GlobalHotkey`.
    """
    required_mods = _parse_modifiers(hotkey)
    last: list[float] = [0.0]  # mutable container so the closure can write to it

    def _guarded() -> None:
        # Extra-modifier guard (same logic as GlobalHotkey._on_pressed)
        if _extra_modifier_held(required_mods):
            return

        # Debounce guard
        now = time.monotonic()
        if now - last[0] < _DEBOUNCE_SECONDS:
            return
        last[0] = now

        callback()

    def _run() -> None:
        import keyboard  # type: ignore[import-untyped]

        keyboard.add_hotkey(hotkey, _guarded, suppress=False)
        keyboard.wait()

    thread = threading.Thread(target=_run, name="aiwriter-hotkey", daemon=True)
    thread.start()
    return thread
