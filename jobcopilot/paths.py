import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def is_serverless() -> bool:
    """Detect whether code is executing in Vercel or AWS Lambda serverless runtime."""
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("VERCEL_ENV")
    )


def get_db_path() -> Path:
    """Return database path. In serverless / read-only runtime, seeds /tmp/jobcopilot.db."""
    env_override = os.environ.get("JOBCOPILOT_DB_PATH")
    if env_override:
        return Path(env_override)

    if is_serverless():
        tmp_db = Path("/tmp") / "jobcopilot.db"
        if not tmp_db.exists():
            seed_db = ROOT / "data" / "jobcopilot.db"
            if seed_db.exists() and seed_db.stat().st_size > 0:
                try:
                    shutil.copy2(seed_db, tmp_db)
                except Exception:
                    pass
            else:
                alt_db = ROOT / "jobcopilot.db"
                if alt_db.exists() and alt_db.stat().st_size > 0:
                    try:
                        shutil.copy2(alt_db, tmp_db)
                    except Exception:
                        pass
        return tmp_db

    return ROOT / "data" / "jobcopilot.db"


def get_profile_path() -> Path:
    """Return profile.yaml path. In serverless runtime, copies seed to /tmp/profile.yaml if needed."""
    if is_serverless():
        tmp_profile = Path("/tmp") / "profile.yaml"
        if not tmp_profile.exists():
            seed_profile = ROOT / "profile" / "profile.yaml"
            if seed_profile.exists():
                try:
                    shutil.copy2(seed_profile, tmp_profile)
                except Exception:
                    pass
        return tmp_profile
    return ROOT / "profile" / "profile.yaml"


def get_resume_path() -> Path:
    """Return resume.md path. In serverless runtime, copies seed to /tmp/resume.md if needed."""
    if is_serverless():
        tmp_resume = Path("/tmp") / "resume.md"
        if not tmp_resume.exists():
            seed_resume = ROOT / "profile" / "resume.md"
            if seed_resume.exists():
                try:
                    shutil.copy2(seed_resume, tmp_resume)
                except Exception:
                    pass
        return tmp_resume
    return ROOT / "profile" / "resume.md"


DATA_DIR = ROOT / "data"
DB_PATH = get_db_path()
PROFILE_PATH = get_profile_path()
RESUME_PATH = get_resume_path()
WATCHLIST_PATH = (
    ROOT / "watchlist.yaml"
    if (ROOT / "watchlist.yaml").exists()
    else ROOT / "config" / "watchlist.yaml"
)
INBOX_DIR = ROOT / "inbox"
STATIC_DIR = Path(__file__).resolve().parent / "static"

