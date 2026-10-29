"""Review-first job copilot for Bangalore software-engineer search."""

from jobcopilot.filters import BANGALORE_HINTS, SOFTWARE_TITLE_HINTS as TITLE_HINTS
from jobcopilot.paths import INBOX_DIR, ROOT, WATCHLIST_PATH

__version__ = "0.1.0"
QUEUE_THRESHOLD = 45

__all__ = [
    "BANGALORE_HINTS",
    "INBOX_DIR",
    "TITLE_HINTS",
    "WATCHLIST_PATH",
    "ROOT",
    "QUEUE_THRESHOLD",
]

