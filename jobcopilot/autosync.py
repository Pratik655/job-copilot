from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from jobcopilot.pipeline import run_pipeline

logger = logging.getLogger("jobcopilot.autosync")

_lock = threading.Lock()
_autosync_state: dict[str, Any] = {
    "enabled": False,
    "interval_minutes": 30,
    "last_sync_time": None,
    "last_sync_result": None,
    "is_syncing": False,
    "last_error": None,
}
_thread: threading.Thread | None = None
_stop_event = threading.Event()


def get_autosync_status() -> dict[str, Any]:
    with _lock:
        return dict(_autosync_state)


def _sync_worker() -> None:
    global _autosync_state
    while not _stop_event.is_set():
        # Check if enabled
        should_run = False
        interval = 30
        with _lock:
            should_run = _autosync_state["enabled"]
            interval = _autosync_state["interval_minutes"]

        if should_run:
            try:
                with _lock:
                    _autosync_state["is_syncing"] = True
                    _autosync_state["last_error"] = None
                result = run_pipeline()
                with _lock:
                    _autosync_state["last_sync_time"] = datetime.now(timezone.utc).isoformat()
                    _autosync_state["last_sync_result"] = result
                    _autosync_state["is_syncing"] = False
            except Exception as e:
                logger.exception("Auto-sync error: %s", e)
                with _lock:
                    _autosync_state["last_error"] = str(e)
                    _autosync_state["is_syncing"] = False

        # Sleep in small slices to respond promptly to stop event
        sleep_seconds = interval * 60
        for _ in range(int(sleep_seconds)):
            if _stop_event.is_set():
                break
            time.sleep(1)


def trigger_sync_now(background: bool = True) -> dict[str, Any]:
    """Execute immediate sync in background thread (default) or foreground."""
    global _autosync_state
    with _lock:
        if _autosync_state["is_syncing"]:
            return {"status": "already_syncing", "state": dict(_autosync_state)}
        _autosync_state["is_syncing"] = True
        _autosync_state["last_error"] = None

    def _execute() -> None:
        try:
            result = run_pipeline()
            with _lock:
                _autosync_state["last_sync_time"] = datetime.now(timezone.utc).isoformat()
                _autosync_state["last_sync_result"] = result
                _autosync_state["is_syncing"] = False
        except Exception as e:
            logger.exception("Auto-sync error: %s", e)
            with _lock:
                _autosync_state["last_error"] = str(e)
                _autosync_state["is_syncing"] = False

    if background:
        thread = threading.Thread(target=_execute, daemon=True)
        thread.start()
        with _lock:
            return {"status": "started_in_background", "state": dict(_autosync_state)}
    else:
        _execute()
        with _lock:
            return {"status": "completed", "state": dict(_autosync_state)}


def set_autosync_enabled(enabled: bool, interval_minutes: int = 30) -> dict[str, Any]:
    global _thread, _autosync_state
    with _lock:
        _autosync_state["enabled"] = enabled
        _autosync_state["interval_minutes"] = max(5, interval_minutes)

    if enabled:
        if _thread is None or not _thread.is_alive():
            _stop_event.clear()
            _thread = threading.Thread(target=_sync_worker, daemon=True)
            _thread.start()
    else:
        _stop_event.set()

    return get_autosync_status()
