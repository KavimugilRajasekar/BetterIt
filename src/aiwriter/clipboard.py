"""Windows clipboard helpers: read the currently selected text, paste text back.

Both functions use ctypes to drive the Windows keyboard and clipboard APIs. They
are blocking and must be called from the GUI thread (the user expects an immediate
response when the hotkey fires, and the simulated Ctrl+C / Ctrl+V is itself
synchronous on Windows).
"""
from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

import pyperclip

# --- Win32 constants and function prototypes --------------------------------

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
CF_UNICODETEXT = 13

# Make keybd_event argument types explicit so 64-bit Python doesn't get confused.
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)]
user32.keybd_event.restype = None

user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND

user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

# --- Tiny helpers -----------------------------------------------------------

NULL = ctypes.c_void_p()


def _send_key(vk: int) -> None:
    """Press and release a single virtual key."""
    user32.keybd_event(vk, 0, 0, NULL)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, NULL)


def _send_combo(*virtual_keys: int) -> None:
    """Press all keys down, then release all keys up."""
    for vk in virtual_keys:
        user32.keybd_event(vk, 0, 0, NULL)
    for vk in reversed(virtual_keys):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, NULL)


# --- Public API -------------------------------------------------------------

def get_foreground_hwnd() -> int:
    """Return the handle of the window the user is currently looking at."""
    return user32.GetForegroundWindow()


def focus_window(hwnd: int) -> None:
    """Bring the given window to the foreground. Best-effort."""
    if hwnd:
        user32.SetForegroundWindow(hwnd)


def read_selected() -> str:
    """Copy the user's current selection to the clipboard and return it.

    Caller is expected to have captured the foreground window's hwnd *before*
    calling this, so the paste-back step can refocus the source app.
    """
    pyperclip.copy("")  # clear so we can detect "nothing was selected"
    _send_combo(VK_CONTROL, ord("C"))
    # Give the source app a moment to populate the clipboard.
    time.sleep(0.08)
    return pyperclip.paste()


def paste_back(text: str) -> None:
    """Write `text` to the clipboard and simulate Ctrl+V in the source app.

    The previous clipboard contents are saved and restored shortly after,
    so the user doesn't lose what they had copied.
    """
    saved = pyperclip.paste()
    try:
        pyperclip.copy(text)
        # Tiny delay to make sure the clipboard is committed before we paste.
        time.sleep(0.05)
        _send_combo(VK_CONTROL, VK_V)
    finally:
        # Restore on a short delay so it doesn't clobber the paste the source
        # app just performed.
        time.sleep(0.15)
        try:
            pyperclip.copy(saved)
        except Exception:
            # If the original clipboard held something exotic (e.g. an image),
            # give up silently — restoring the user's text is better than
            # leaving them with a broken clipboard state.
            pass
