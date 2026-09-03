from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "jobcopilot.db"
PROFILE_PATH = ROOT / "profile" / "profile.yaml"
RESUME_PATH = ROOT / "profile" / "resume.md"
WATCHLIST_PATH = ROOT / "config" / "watchlist.yaml"
INBOX_DIR = ROOT / "inbox"
TEMPLATES_DIR = Path(__file__).resolve().parent / "web" / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "web" / "static"
