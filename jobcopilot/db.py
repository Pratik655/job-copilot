from __future__ import annotations

import csv
import io
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from jobcopilot.filters import (
    detect_domain,
    detect_experience_level,
    normalize_city,
)
from jobcopilot.paths import get_db_path
from jobcopilot.settings import ROOT

DB_PATH = get_db_path()


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    target_path = get_db_path()
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    conn = sqlite3.connect(target_path, timeout=60.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                posted_at TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                score REAL DEFAULT NULL,
                score_json TEXT NOT NULL DEFAULT '',
                applied_at TEXT DEFAULT NULL,
                snoozed_until TEXT DEFAULT NULL,
                ingested_at TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL DEFAULT '',
                domain_key TEXT NOT NULL DEFAULT 'software',
                experience_level TEXT NOT NULL DEFAULT 'Fresher / Entry-Level',
                match_breakdown TEXT NOT NULL DEFAULT '{}',
                skills_matched TEXT NOT NULL DEFAULT '[]',
                UNIQUE(source, source_id)
            );

            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL UNIQUE,
                cover_letter TEXT NOT NULL DEFAULT '',
                resume_bullets TEXT NOT NULL DEFAULT '[]',
                screening_answers TEXT NOT NULL DEFAULT '{}',
                referral_message TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                company TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                applied_at TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );
            """
        )

        # Dynamic migration for existing databases
        cursor = conn.execute("PRAGMA table_info(jobs)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        cols_to_add = {
            "city": "TEXT NOT NULL DEFAULT ''",
            "domain": "TEXT NOT NULL DEFAULT ''",
            "domain_key": "TEXT NOT NULL DEFAULT 'software'",
            "experience_level": "TEXT NOT NULL DEFAULT 'Fresher / Entry-Level'",
            "match_breakdown": "TEXT NOT NULL DEFAULT '{}'",
            "skills_matched": "TEXT NOT NULL DEFAULT '[]'",
        }
        for col, col_def in cols_to_add.items():
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} {col_def}")


def backfill_metadata(force: bool = False) -> int:
    """Populate city, domain, and experience_level for any jobs missing them or if forced/legacy."""
    updated = 0
    with connect() as conn:
        legacy_keys = ("backend", "cloud_devops", "fullstack", "security", "qa_sdet", "data_ai")
        placeholders = ",".join("?" for _ in legacy_keys)
        if force:
            rows = conn.execute(
                "SELECT id, title, location, description, city, domain, experience_level FROM jobs"
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT id, title, location, description, city, domain, experience_level FROM jobs WHERE city = '' OR domain = '' OR domain_key IN ({placeholders})",
                legacy_keys,
            ).fetchall()
        for r in rows:
            city = normalize_city(r["location"], r["description"])
            dom_key, dom_label = detect_domain(r["title"], r["description"])
            exp = detect_experience_level(r["title"], r["description"])
            conn.execute(
                "UPDATE jobs SET city = ?, domain = ?, domain_key = ?, experience_level = ? WHERE id = ?",
                (city, dom_label, dom_key, exp, r["id"]),
            )
            updated += 1
        conn.commit()
    return updated


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def was_applied(conn: sqlite3.Connection, job: dict[str, Any]) -> bool:
    url = job.get("url")
    if url:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE url = ? AND status = 'applied' LIMIT 1", (url,)
        ).fetchone()
        if row:
            return True
        row = conn.execute("SELECT 1 FROM applications WHERE url = ? LIMIT 1", (url,)).fetchone()
        if row:
            return True
    source = job.get("source") or "ats"
    source_id = str(job.get("external_id") or job.get("source_id") or "")
    if source_id:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE source = ? AND source_id = ? AND status = 'applied' LIMIT 1",
            (source, source_id),
        ).fetchone()
        if row:
            return True
    return False


def upsert_job(conn: sqlite3.Connection, job: dict[str, Any]) -> tuple[int, bool]:
    source = job.get("source") or "ats"
    source_id = str(job.get("external_id") or job.get("source_id") or "")
    provider = job.get("provider") or ""
    company = job.get("company") or ""
    title = job.get("title") or ""
    location = job.get("location") or ""
    url = job.get("url") or ""
    description = job.get("description") or ""
    posted_at = job.get("posted_at")
    now = utcnow()

    # Compute enriched metadata
    city = normalize_city(location, description)
    dom_key, dom_label = detect_domain(title, description)
    exp_level = detect_experience_level(title, description)

    existing = conn.execute(
        "SELECT id, status FROM jobs WHERE source = ? AND source_id = ?",
        (source, source_id),
    ).fetchone()

    if not existing and url:
        existing = conn.execute(
            "SELECT id, status FROM jobs WHERE url = ? AND url != ''",
            (url,),
        ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE jobs SET
                company = ?,
                title = ?,
                location = ?,
                url = ?,
                description = ?,
                posted_at = COALESCE(?, posted_at),
                city = ?,
                domain = ?,
                domain_key = ?,
                experience_level = ?
            WHERE id = ?
            """,
            (company, title, location, url, description, posted_at, city, dom_label, dom_key, exp_level, existing["id"]),
        )
        return int(existing["id"]), False

    cursor = conn.execute(
        """
        INSERT INTO jobs (
            source, source_id, provider, company, title, location, url, description,
            posted_at, status, ingested_at, city, domain, domain_key, experience_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?, ?, ?)
        """,
        (source, source_id, provider, company, title, location, url, description, posted_at, now, city, dom_label, dom_key, exp_level),
    )
    return int(cursor.lastrowid), True


def save_score(
    conn: sqlite3.Connection,
    job_id: int,
    score: int,
    result: dict[str, Any],
    status: str,
) -> None:
    score_json = dumps(result)
    match_breakdown = dumps(result.get("match_breakdown") or {})
    skills_matched = dumps(result.get("skills_matched") or [])
    conn.execute(
        """
        UPDATE jobs SET
            score = ?,
            score_json = ?,
            status = ?,
            match_breakdown = ?,
            skills_matched = ?
        WHERE id = ?
        """,
        (score, score_json, status, match_breakdown, skills_matched, job_id),
    )


def save_draft(conn: sqlite3.Connection, job_id: int, draft: dict[str, Any]) -> None:
    cover_letter = draft.get("cover_letter") or ""
    bullets = (
        dumps(draft.get("resume_bullets") or [])
        if not isinstance(draft.get("resume_bullets"), str)
        else draft.get("resume_bullets")
    )
    screening = (
        dumps(draft.get("screening_answers") or {})
        if not isinstance(draft.get("screening_answers"), str)
        else draft.get("screening_answers")
    )
    referral = draft.get("referral_message") or ""
    now = utcnow()

    conn.execute(
        """
        INSERT INTO drafts (job_id, cover_letter, resume_bullets, screening_answers, referral_message, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            cover_letter = excluded.cover_letter,
            resume_bullets = excluded.resume_bullets,
            screening_answers = excluded.screening_answers,
            referral_message = excluded.referral_message,
            updated_at = excluded.updated_at
        """,
        (job_id, cover_letter, bullets, screening, referral, now),
    )


def get_job(conn: sqlite3.Connection, job_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT j.*,
               d.cover_letter, d.resume_bullets, d.screening_answers, d.referral_message
        FROM jobs j
        LEFT JOIN drafts d ON j.id = d.job_id
        WHERE j.id = ?
        """,
        (job_id,),
    ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["draft"] = {
        "cover_letter": data.pop("cover_letter", None),
        "resume_bullets": data.pop("resume_bullets", None),
        "screening_answers": data.pop("screening_answers", None),
        "referral_message": data.pop("referral_message", None),
    }
    return data


def list_jobs(
    conn: sqlite3.Connection,
    status: str | None = None,
    city: str | None = None,
    domain: str | None = None,
    search: str | None = None,
    min_score: int | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT j.*,
               d.cover_letter, d.resume_bullets, d.screening_answers, d.referral_message
        FROM jobs j
        LEFT JOIN drafts d ON j.id = d.job_id
        WHERE 1=1
    """
    params: list[Any] = []

    if status:
        query += " AND j.status = ?"
        params.append(status)

    if city:
        query += " AND (j.city LIKE ? OR j.location LIKE ?)"
        params.append(f"%{city}%")
        params.append(f"%{city}%")

    if domain:
        query += " AND (j.domain_key = ? OR j.domain LIKE ?)"
        params.append(domain)
        params.append(f"%{domain}%")

    if min_score is not None:
        query += " AND j.score >= ?"
        params.append(min_score)

    if search:
        s = f"%{search.strip().lower()}%"
        query += """ AND (
            LOWER(j.title) LIKE ? OR
            LOWER(j.company) LIKE ? OR
            LOWER(j.city) LIKE ? OR
            LOWER(j.domain) LIKE ? OR
            LOWER(j.skills_matched) LIKE ? OR
            LOWER(j.description) LIKE ?
        )"""
        params.extend([s, s, s, s, s, s])

    query += " ORDER BY j.score DESC NULLS LAST, j.id DESC"

    rows = conn.execute(query, params).fetchall()
    results = []
    for r in rows:
        data = dict(r)
        data["draft"] = {
            "cover_letter": data.pop("cover_letter", None),
            "resume_bullets": data.pop("resume_bullets", None),
            "screening_answers": data.pop("screening_answers", None),
            "referral_message": data.pop("referral_message", None),
        }
        results.append(data)
    return results


def get_available_filters(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return distinct cities, domains, experience levels, and statuses with counts."""
    city_rows = conn.execute(
        "SELECT city, count(*) as count FROM jobs WHERE city != '' GROUP BY city ORDER BY count DESC"
    ).fetchall()
    domain_rows = conn.execute(
        "SELECT domain_key, domain, count(*) as count FROM jobs WHERE domain != '' GROUP BY domain_key ORDER BY count DESC"
    ).fetchall()
    exp_rows = conn.execute(
        "SELECT experience_level, count(*) as count FROM jobs WHERE experience_level != '' GROUP BY experience_level ORDER BY count DESC"
    ).fetchall()
    status_rows = conn.execute(
        "SELECT status, count(*) as count FROM jobs GROUP BY status"
    ).fetchall()

    return {
        "cities": [{"city": r["city"], "count": r["count"]} for r in city_rows],
        "domains": [{"key": r["domain_key"], "label": r["domain"], "count": r["count"]} for r in domain_rows],
        "experience_levels": [{"level": r["experience_level"], "count": r["count"]} for r in exp_rows],
        "statuses": {r["status"]: r["count"] for r in status_rows},
    }


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT status, count(*) as c FROM jobs GROUP BY status").fetchall()
    res = {k: 0 for k in ("queued", "ready", "applied", "snoozed", "skipped", "new")}
    for r in rows:
        res[r["status"]] = r["c"]
    return res


def set_status(
    conn: sqlite3.Connection,
    job_id: int,
    status: str,
    until: str | None = None,
) -> None:
    conn.execute(
        "UPDATE jobs SET status = ?, snoozed_until = ? WHERE id = ?",
        (status, until, job_id),
    )


def record_applied(conn: sqlite3.Connection, job_id: int, notes: str = "") -> None:
    now = utcnow()
    conn.execute("UPDATE jobs SET status = 'applied', applied_at = ? WHERE id = ?", (now, job_id))
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job:
        conn.execute(
            """
            INSERT INTO applications (job_id, company, title, url, applied_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_id, job["company"], job["title"], job["url"], now, notes),
        )


def list_apply_history(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM applications ORDER BY applied_at DESC").fetchall()
    return [dict(r) for r in rows]


def export_jobs_data(conn: sqlite3.Connection, status: str | None = None, fmt: str = "csv") -> str:
    """Export jobs into CSV string or JSON string."""
    jobs = list_jobs(conn, status=status)
    if fmt == "json":
        return json.dumps(jobs, indent=2, ensure_ascii=False)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Company", "Title", "City", "Location", "Domain", "Experience Level",
        "Score", "Status", "Applied At", "URL", "Cover Letter"
    ])
    for j in jobs:
        draft = j.get("draft") or {}
        writer.writerow([
            j.get("id"),
            j.get("company"),
            j.get("title"),
            j.get("city"),
            j.get("location"),
            j.get("domain"),
            j.get("experience_level"),
            j.get("score"),
            j.get("status"),
            j.get("applied_at") or "",
            j.get("url"),
            (draft.get("cover_letter") or "").replace("\n", " "),
        ])
    return output.getvalue()
