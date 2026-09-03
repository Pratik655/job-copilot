from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from jobcopilot.db import (
    connect,
    counts,
    get_job,
    init_db,
    list_apply_history,
    list_jobs,
    record_applied,
    save_draft,
    set_status,
)
from jobcopilot.profile import load_profile
from jobcopilot.ingest import backfill_plain_descriptions, html_to_text, ingest_paste
from jobcopilot.pipeline import process_new_jobs, run_pipeline

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Job copilot")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class PasteIn(BaseModel):
    text: str = Field(min_length=20)
    url: str | None = None


class DraftIn(BaseModel):
    cover_letter: str | None = None
    resume_bullets: list[str] | None = None
    screening_answers: dict[str, str] | None = None
    referral_message: str | None = None


def _serialize(job: dict) -> dict:
    draft = job.get("draft")
    if draft:
        bullets = draft.get("resume_bullets")
        screening = draft.get("screening_answers")
        try:
            draft["resume_bullets"] = json.loads(bullets) if isinstance(bullets, str) else bullets
        except json.JSONDecodeError:
            draft["resume_bullets"] = []
        try:
            draft["screening_answers"] = json.loads(screening) if isinstance(screening, str) else screening
        except json.JSONDecodeError:
            draft["screening_answers"] = {}
    score_json = job.get("score_json")
    if isinstance(score_json, str) and score_json:
        try:
            job["score_json"] = json.loads(score_json)
        except json.JSONDecodeError:
            pass
    if job.get("description"):
        job["description"] = html_to_text(job["description"])
    return job


@app.on_event("startup")
def startup() -> None:
    init_db()
    backfill_plain_descriptions()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/me")
def api_me() -> dict:
    profile = load_profile()
    return {
        "name": profile.get("name"),
        "headline": profile.get("headline"),
        "target_location": profile.get("target_location"),
    }


@app.get("/api/stats")
def api_stats() -> dict:
    with connect() as conn:
        return counts(conn)


@app.get("/api/jobs")
def api_jobs(status: str | None = None) -> list[dict]:
    with connect() as conn:
        return [_serialize(j) for j in list_jobs(conn, status)]


@app.get("/api/jobs/{job_id}")
def api_job(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _serialize(job)


@app.post("/api/inbox")
def api_inbox(body: PasteIn) -> dict:
    result = ingest_paste(body.text, body.url)
    process_new_jobs()
    with connect() as conn:
        job = get_job(conn, result["id"])
    return {"ingest": result, "job": _serialize(job) if job else None}


@app.post("/api/run")
def api_run() -> dict:
    return run_pipeline()


@app.patch("/api/jobs/{job_id}/draft")
def api_edit_draft(job_id: int, body: DraftIn) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        current = job.get("draft") or {}
        bullets = body.resume_bullets
        if bullets is None:
            raw = current.get("resume_bullets")
            bullets = json.loads(raw) if isinstance(raw, str) and raw else (raw or [])
        screening = body.screening_answers
        if screening is None:
            raw = current.get("screening_answers")
            screening = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
        save_draft(
            conn,
            job_id,
            {
                "cover_letter": body.cover_letter if body.cover_letter is not None else current.get("cover_letter"),
                "resume_bullets": bullets,
                "screening_answers": screening,
                "referral_message": body.referral_message
                if body.referral_message is not None
                else current.get("referral_message"),
            },
        )
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.post("/api/jobs/{job_id}/approve")
def api_approve(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        set_status(conn, job_id, "ready")
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.get("/api/history")
def api_history() -> list[dict]:
    with connect() as conn:
        return list_apply_history(conn)


@app.post("/api/jobs/{job_id}/applied")
def api_applied(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        record_applied(conn, job_id)
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.post("/api/jobs/{job_id}/skip")
def api_skip(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        set_status(conn, job_id, "skipped")
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.post("/api/jobs/{job_id}/snooze")
def api_snooze(job_id: int) -> dict:
    until = (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0).isoformat()
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        set_status(conn, job_id, "snoozed", until)
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.get("/open/{job_id}")
def open_job(job_id: int) -> RedirectResponse:
    with connect() as conn:
        job = get_job(conn, job_id)
    if not job or not job.get("url"):
        raise HTTPException(404, "No apply URL")
    return RedirectResponse(job["url"])


def create_app() -> FastAPI:
    return app
