from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

from jobcopilot import (
    BANGALORE_HINTS,
    INBOX_DIR,
    TITLE_HINTS,
    WATCHLIST_PATH,
)
from jobcopilot.db import connect, init_db, upsert_job, was_applied

USER_AGENT = "job-copilot/0.1 (personal job search; +https://github.com/abhijeetkr0202/job-copilot)"
PER_COMPANY_CAP = 20

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}


def html_to_text(value: str | None) -> str:
    """Turn ATS HTML (often entity-escaped) into readable plain text."""
    if not value:
        return ""
    text = str(value)
    for _ in range(4):
        next_text = html.unescape(text)
        if next_text == text:
            break
        text = next_text
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|section|article|ul|ol)>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _strip_html(value: str | None) -> str:
    return html_to_text(value)


def backfill_plain_descriptions() -> int:
    updated = 0
    with connect() as conn:
        rows = conn.execute("SELECT id, description FROM jobs").fetchall()
        for row in rows:
            cleaned = html_to_text(row["description"])
            if cleaned != (row["description"] or ""):
                conn.execute("UPDATE jobs SET description = ? WHERE id = ?", (cleaned, row["id"]))
                updated += 1
    return updated


def _matches_title(title: str) -> bool:
    lowered = title.lower()
    if re.search(r"\bintern(ship)?\b", lowered) and "internal" not in lowered:
        return False
    return any(hint in lowered for hint in TITLE_HINTS)


def _matches_location(location: str | None, description: str = "") -> bool:
    loc = (location or "").lower()
    if any(hint in loc for hint in BANGALORE_HINTS):
        return True
    if "india" in loc and "indiana" not in loc:
        return True
    blob = f"{loc} {description or ''}".lower()
    if "remote" in loc and ("india" in blob or any(hint in blob for hint in BANGALORE_HINTS)):
        return True
    return False


def load_watchlist(path: Path | None = None) -> list[dict[str, str]]:
    data = yaml.safe_load((path or WATCHLIST_PATH).read_text()) or {}
    return list(data.get("companies") or [])


def fetch_company(client: httpx.Client, company: dict[str, str]) -> list[dict[str, Any]]:
    ats = company["ats"]
    slug = company["slug"]
    name = company["name"]
    url = ENDPOINTS[ats].format(slug=slug)
    response = client.get(url, timeout=20.0)
    if response.status_code != 200:
        return []
    payload = response.json()
    jobs: list[dict[str, Any]] = []
    if ats == "greenhouse":
        for item in payload.get("jobs") or []:
            loc = ((item.get("location") or {}).get("name")) or ""
            jobs.append(
                {
                    "source": "ats",
                    "provider": "greenhouse",
                    "external_id": str(item.get("id")),
                    "company": name,
                    "title": item.get("title") or "",
                    "location": loc,
                    "url": item.get("absolute_url"),
                    "description": _strip_html(item.get("content")),
                    "posted_at": item.get("first_published") or item.get("updated_at"),
                }
            )
    elif ats == "lever":
        for item in payload or []:
            cats = item.get("categories") or {}
            jobs.append(
                {
                    "source": "ats",
                    "provider": "lever",
                    "external_id": str(item.get("id")),
                    "company": name,
                    "title": item.get("text") or "",
                    "location": cats.get("location") or "",
                    "url": item.get("hostedUrl") or item.get("applyUrl"),
                    "description": _strip_html(item.get("descriptionPlain") or item.get("description")),
                    "posted_at": (
                        datetime.fromtimestamp(item["createdAt"] / 1000, tz=timezone.utc).isoformat()
                        if item.get("createdAt")
                        else None
                    ),
                }
            )
    elif ats == "ashby":
        listings = payload.get("jobs") or payload.get("jobPostings") or []
        for item in listings:
            if item.get("isListed") is False:
                continue
            loc = item.get("location") or ""
            if isinstance(loc, dict):
                loc = loc.get("name") or ""
            jobs.append(
                {
                    "source": "ats",
                    "provider": "ashby",
                    "external_id": str(item.get("id")),
                    "company": name,
                    "title": item.get("title") or "",
                    "location": loc,
                    "url": item.get("jobUrl") or item.get("applyUrl"),
                    "description": _strip_html(item.get("descriptionHtml") or item.get("descriptionPlain")),
                    "posted_at": item.get("publishedAt"),
                }
            )
    matched = [
        j
        for j in jobs
        if _matches_title(j["title"]) and _matches_location(j["location"], j.get("description") or "")
    ]
    bangalore_first = sorted(
        matched,
        key=lambda j: (0 if any(h in (j["location"] or "").lower() for h in BANGALORE_HINTS) else 1, j["title"]),
    )
    return bangalore_first[:PER_COMPANY_CAP]


def ingest_watchlist() -> dict[str, int]:
    init_db()
    inserted = 0
    updated = 0
    already_applied = 0
    failed = 0
    companies = load_watchlist()
    with httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
        fetched: list[dict[str, Any]] = []
        for company in companies:
            try:
                fetched.extend(fetch_company(client, company))
            except Exception:
                failed += 1
    with connect() as conn:
        for job in fetched:
            applied = was_applied(conn, job)
            _, is_new = upsert_job(conn, job)
            if applied:
                already_applied += 1
            elif is_new:
                inserted += 1
            else:
                updated += 1
    return {
        "inserted": inserted,
        "updated": updated,
        "already_applied": already_applied,
        "failed_companies": failed,
        "fetched": len(fetched),
    }


def parse_paste(raw: str, url: str | None = None) -> dict[str, Any]:
    text = raw.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else "Pasted role"
    company = "Unknown"
    for line in lines[:8]:
        lowered = line.lower()
        if lowered.startswith("company:"):
            company = line.split(":", 1)[1].strip()
            break
        if lowered.startswith("at ") and len(line) < 80:
            company = line[3:].strip()
            break
    location = ""
    extracted_url = url
    for line in lines[:20]:
        lowered = line.lower()
        if lowered.startswith("url:"):
            extracted_url = line.split(":", 1)[1].strip() or extracted_url
            continue
        if lowered.startswith("http"):
            continue
        if any(h in lowered for h in BANGALORE_HINTS + ("remote", "hybrid", "india")):
            location = line
            break
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    provider = "paste"
    if extracted_url:
        host = urlparse(extracted_url).netloc.lower()
        if "linkedin" in host:
            provider = "linkedin"
        elif "naukri" in host:
            provider = "naukri"
        elif "indeed" in host or "glassdoor" in host:
            provider = "indeed"
        elif "wellfound" in host or "angel.co" in host:
            provider = "wellfound"
    return {
        "source": "paste",
        "provider": provider,
        "external_id": digest,
        "company": company,
        "title": title[:180],
        "location": location or "Bangalore",
        "url": extracted_url,
        "description": text,
        "posted_at": None,
    }


def ingest_paste(raw: str, url: str | None = None) -> dict[str, Any]:
    init_db()
    job = parse_paste(raw, url)
    with connect() as conn:
        applied = was_applied(conn, job)
        job_id, is_new = upsert_job(conn, job)
    return {
        "id": job_id,
        "created": is_new,
        "already_applied": applied,
        **{k: job[k] for k in ("title", "company", "provider")},
    }


def ingest_inbox() -> dict[str, int]:
    init_db()
    inserted = 0
    skipped = 0
    for path in sorted(INBOX_DIR.glob("*")):
        if path.name.startswith(".") or path.suffix.lower() not in {".md", ".txt"}:
            continue
        text = path.read_text()
        url = None
        for line in text.splitlines():
            if line.lower().startswith("url:"):
                url = line.split(":", 1)[1].strip()
                break
        result = ingest_paste(text, url)
        if result["created"]:
            inserted += 1
        else:
            skipped += 1
    return {"inserted": inserted, "updated": skipped}
