from __future__ import annotations

from jobcopilot.ai import score_and_draft
from jobcopilot.db import connect, init_db, save_draft, save_score
from jobcopilot.ingest import ingest_inbox, ingest_watchlist
from jobcopilot.profile import load_profile


def process_new_jobs() -> dict[str, int]:
    init_db()
    profile = load_profile()
    queued = 0
    skipped = 0
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs WHERE status = 'new'").fetchall()
        for row in rows:
            job = dict(row)
            result = score_and_draft(job, profile)
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
    return {"queued": queued, "skipped": skipped, "processed": queued + skipped}


def run_pipeline() -> dict[str, object]:
    ats = ingest_watchlist()
    inbox = ingest_inbox()
    scored = process_new_jobs()
    return {"ats": ats, "inbox": inbox, "scored": scored}
