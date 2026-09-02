"""Single-instance enforcement for BetterIt.

Uses a Windows named mutex to detect a running instance.  If one is found,
that process is terminated gracefully (SIGTERM → wait 3 s → SIGKILL) before
the current process continues.

Works identically whether launched as ``python run.py`` or as the built
``BetterIt.exe``, because the mutex name is process-name-agnostic.

Usage (call once, as early as possible in the entry point)::

    from aiwriter.single_instance import ensure_single_instance
    ensure_single_instance()
"""

from __future__ import annotations

import os
import sys
import time

# The mutex name is stable across py / exe launches.
_MUTEX_NAME = "Global\\BetterIt_SingleInstance_Mutex"

# PID file kept next to the running instance so we can find the old PID.
# We store it in %LOCALAPPDATA%\BetterIt\ so it survives across restarts and
# is writable both in dev mode and when running as a built exe.
def _pid_path() -> str:
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    folder = os.path.join(base, "BetterIt")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "betterit.pid")


def _write_pid() -> None:
    try:
        with open(_pid_path(), "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def _read_old_pid() -> int | None:
    try:
        with open(_pid_path()) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _kill_old_instance(pid: int) -> None:
    """Terminate *pid* gracefully then forcefully if it doesn't exit in time."""
    import ctypes
    import ctypes.wintypes

    PROCESS_TERMINATE = 0x0001
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    SYNCHRONIZE = 0x00100000

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

    # Open with enough rights to wait + terminate.
    handle = kernel32.OpenProcess(
        PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE,
        False,
        pid,
    )
    if not handle:
        return  # process already gone

    try:
        # Graceful: ask the process to exit via WM_CLOSE broadcast first.
        # (Works for Qt apps that handle WM_CLOSE to quit.)
        _send_wm_close(pid)

        # Wait up to 3 s for graceful exit.
        result = kernel32.WaitForSingleObject(handle, 3000)
        if result != 0:  # WAIT_OBJECT_0 == 0
            # Still alive → force-kill.
            kernel32.TerminateProcess(handle, 1)
            kernel32.WaitForSingleObject(handle, 2000)
    finally:
        kernel32.CloseHandle(handle)


def _send_wm_close(pid: int) -> None:
    """Post WM_CLOSE to all top-level windows owned by *pid*."""
    import ctypes
    import ctypes.wintypes

    WM_CLOSE = 0x0010
    HWND_BROADCAST = 0xFFFF

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
    )

    def _callback(hwnd: int, _lparam: int) -> bool:
        win_pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))
        if win_pid.value == pid:
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return True  # continue enumeration

    user32.EnumWindows(EnumWindowsProc(_callback), 0)


def ensure_single_instance() -> None:
    """Enforce a single running BetterIt instance.

    * If no previous instance is running → create mutex + write PID file,
      then return normally so the caller proceeds with startup.
    * If a previous instance IS running → kill it, then proceed.

    Idempotent: safe to call more than once in the same process (e.g. from
    both ``run.py`` and ``AIWriterApp.__init__``).  Only the first call does
    real work; subsequent calls return immediately.

    Must be called before ``QApplication`` is created so the GUI never
    flickers from the old instance during the handover.
    """
    # Guard: don't run twice in the same process.
    if globals().get("_INSTANCE_CHECKED"):
        return
    globals()["_INSTANCE_CHECKED"] = True

    import ctypes
    import ctypes.wintypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

    # Try to create the mutex.
    ERROR_ALREADY_EXISTS = 183

    handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        # Another instance holds the mutex — find and kill it.
        old_pid = _read_old_pid()
        if old_pid and old_pid != os.getpid():
            print(
                f"[BetterIt] Previous instance detected (PID {old_pid}). "
                "Stopping it…",
                file=sys.stderr,
            )
            _kill_old_instance(old_pid)
            # Give Windows a moment to release the old mutex.
            time.sleep(0.4)

        # Release the stale handle and re-create so WE own it now.
        if handle:
            kernel32.CloseHandle(handle)

        handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if not handle:
            # Very unlikely — just continue anyway.
            print("[BetterIt] Warning: could not create instance mutex.", file=sys.stderr)
    else:
        # We are the first instance — take ownership.
        if handle:
            kernel32.ReleaseMutex(handle)   # release the initial lock
            # Re-acquire with bInitialOwner=True so we truly own it.
            kernel32.CloseHandle(handle)
            handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

    # Store the handle on the module so it isn't garbage-collected / closed
    # for the lifetime of this process.
    _MUTEX_HANDLE = handle  # noqa: F841 (intentionally module-level side-effect)
    globals()["_MUTEX_HANDLE"] = handle

    # Record our PID so the next launch can find us.
    _write_pid()
