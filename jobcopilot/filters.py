from __future__ import annotations

SOFTWARE_TITLE_HINTS = (
    "software",
    "engineer",
    "developer",
    "sde",
    "backend",
    "front end",
    "frontend",
    "full stack",
    "fullstack",
    "platform",
    "infrastructure",
    "sre",
    "devops",
    "mobile",
    "android",
    "ios",
    "ml engineer",
    "machine learning engineer",
    "data engineer",
    "staff engineer",
    "principal engineer",
)

BANGALORE_HINTS = ("bangalore", "bengaluru", "blr")
INDIA_HINTS = (
    "india",
    "indian",
    "karnataka",
    "hyderabad",
    "pune",
    "mumbai",
    "gurgaon",
    "gurugram",
    "noida",
    "chennai",
    "delhi",
)
REMOTE_HINTS = ("remote", "hybrid", "anywhere")
EXCLUDE_TITLE_HINTS = (
    "account executive",
    "sales",
    "recruiter",
    "talent acquisition",
    "marketing",
    "customer success",
    "legal counsel",
    "attorney",
)


def _blob(*parts: str | None) -> str:
    return " ".join(p or "" for p in parts).lower()


def is_software_title(title: str | None) -> bool:
    t = (title or "").lower()
    if not t:
        return False
    if any(x in t for x in EXCLUDE_TITLE_HINTS) and not any(
        x in t for x in ("engineer", "developer", "sde")
    ):
        return False
    return any(h in t for h in SOFTWARE_TITLE_HINTS)


def is_bangalore_relevant(location: str | None, description: str | None) -> bool:
    text = _blob(location, (description or "")[:4000])
    if any(h in text for h in BANGALORE_HINTS):
        return True
    loc = (location or "").lower()
    if any(h in loc for h in INDIA_HINTS):
        return True
    if "india" in text and any(h in text for h in REMOTE_HINTS):
        return True
    return False


def keep_job(title: str | None, location: str | None, description: str | None) -> bool:
    return is_software_title(title) and is_bangalore_relevant(location, description)
