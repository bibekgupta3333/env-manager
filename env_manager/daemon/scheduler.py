"""Background scheduler for periodic scans."""

import logging
import threading
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from env_manager.adapters.registry import AdapterRegistry
from env_manager.discovery.scanner import Scanner
from env_manager.storage.database import get_connection

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_scheduler_lock = threading.Lock()


def start_scheduler(db_path: str) -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            return
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            lambda: _run_periodic_scan(db_path),
            "interval",
            hours=24,
            id="periodic_scan",
        )
        _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            _scheduler.shutdown(wait=False)
            _scheduler = None


def _run_periodic_scan(db_path: str) -> None:
    """Run a periodic scan in the background."""
    try:
        conn = get_connection(db_path)
        registry = AdapterRegistry(conn)
        adapters = registry.get_all_enabled()
        scanner = Scanner(conn, adapters)
        scanner.scan(str(Path.home() / "projects"), depth=3)
    except Exception:
        logger.debug("periodic scan failed", exc_info=True)
