from __future__ import annotations

from typing import Any

from jobcopilot.ai import _heuristic, score_and_draft
from jobcopilot.db import backfill_metadata, connect, get_job, init_db, save_draft, save_score
from jobcopilot.ingest import ingest_inbox, ingest_watchlist
from jobcopilot.profile import load_profile


def _profile_to_dict(profile: Any) -> dict[str, Any]:
    if isinstance(profile, dict):
        return profile
    if hasattr(profile, "to_dict"):
        return profile.to_dict()
    return vars(profile) if hasattr(profile, "__dict__") else {}


def process_new_jobs() -> dict[str, int]:
    init_db()
    backfill_metadata()
    profile = _profile_to_dict(load_profile())
    queued = 0
    skipped = 0
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs WHERE status = 'new'").fetchall()
        for row in rows:
            job = dict(row)
            result = _heuristic(job, profile)
            status = "queued" if result.get("decision") == "queue" else "skipped"
            save_score(conn, job["id"], int(result.get("score") or 0), result, status)
            save_draft(
                conn,
                job["id"],
                {
                    "cover_letter": result.get("cover_letter"),
                    "resume_bullets": result.get("resume_bullets") or [],
                    "screening_answers": result.get("screening_answers") or {},
                    "referral_message": result.get("referral_message"),
                },
            )
            if status == "queued":
                queued += 1
            else:
                skipped += 1
        conn.commit()
    return {"queued": queued, "skipped": skipped, "processed": queued + skipped}


def rescore_all_jobs() -> dict[str, int]:
    """Re-score all jobs instantly against the candidate profile and multi-city scoring engine."""
    init_db()
    backfill_metadata()
    profile = _profile_to_dict(load_profile())
    queued = 0
    skipped = 0
    with connect() as conn:
        # Don't overwrite jobs the user explicitly applied to or snoozed
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status NOT IN ('applied', 'snoozed')"
        ).fetchall()
        for row in rows:
            job = dict(row)
            result = _heuristic(job, profile)
            status = "queued" if result.get("decision") == "queue" else "skipped"
            # If job was already ready (approved), keep it ready
            if row["status"] == "ready":
                status = "ready"
            save_score(conn, job["id"], int(result.get("score") or 0), result, status)
            save_draft(
                conn,
                job["id"],
                {
                    "cover_letter": result.get("cover_letter"),
                    "resume_bullets": result.get("resume_bullets") or [],
                    "screening_answers": result.get("screening_answers") or {},
                    "referral_message": result.get("referral_message"),
                },
            )
            if status in ("queued", "ready"):
                queued += 1
            else:
                skipped += 1
        conn.commit()
    return {"queued": queued, "skipped": skipped, "total_rescored": queued + skipped}


def rescore_single_job(job_id: int) -> dict[str, Any] | None:
    """Re-score a single job and update its drafts."""
    init_db()
    profile = load_profile()
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            return None
        result = score_and_draft(job, profile)
        status = "queued" if result.get("decision") == "queue" else "skipped"
        if job["status"] in ("applied", "ready", "snoozed"):
            status = job["status"]
        save_score(conn, job_id, int(result.get("score") or 0), result, status)
        save_draft(
            conn,
            job_id,
            {
                "cover_letter": result.get("cover_letter"),
                "resume_bullets": result.get("resume_bullets") or [],
                "screening_answers": result.get("screening_answers") or {},
                "referral_message": result.get("referral_message"),
            },
        )
        conn.commit()
        return get_job(conn, job_id)


def run_pipeline() -> dict[str, object]:
    ats = ingest_watchlist()
    inbox = ingest_inbox()
    scored = process_new_jobs()
    return {"ats": ats, "inbox": inbox, "scored": scored}
