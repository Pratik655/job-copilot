from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from jobcopilot.ai import get_ai_status
from jobcopilot.autosync import (
    get_autosync_status,
    set_autosync_enabled,
    trigger_sync_now,
)
from jobcopilot.db import (
    backfill_metadata,
    connect,
    counts,
    export_jobs_data,
    get_available_filters,
    get_job,
    init_db,
    list_apply_history,
    list_jobs,
    record_applied,
    save_draft,
    set_status,
)
from jobcopilot.paths import get_resume_path
from jobcopilot.profile import load_profile, save_profile
from jobcopilot.ingest import backfill_plain_descriptions, html_to_text, ingest_paste
from jobcopilot.pipeline import process_new_jobs, rescore_all_jobs, rescore_single_job, run_pipeline
from jobcopilot.resume_parser import (
    AVAILABLE_DOMAINS,
    INDIAN_TECH_CITIES,
    extract_text_from_bytes,
    parse_resume_text,
    save_parsed_profile,
)
from jobcopilot.settings import ROOT

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Job Copilot - Multi-Domain & Multi-City Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class PasteIn(BaseModel):
    text: str = Field(min_length=20)
    url: str | None = None


class DraftIn(BaseModel):
    cover_letter: str | None = None
    resume_bullets: list[str] | None = None
    screening_answers: dict[str, str] | None = None
    referral_message: str | None = None


class TextScanIn(BaseModel):
    text: str = Field(min_length=10)


class ResumeSaveIn(BaseModel):
    parsed: dict[str, Any]
    raw_text: str | None = None
    rescore: bool = False
    trigger_sync: bool = False


class AutoSyncToggleIn(BaseModel):
    enabled: bool
    interval_minutes: int = 30


class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    target_location: str | None = None
    open_to: list[str] | None = None
    target_domains: list[str] | None = None
    target_titles: list[str] | None = None
    stack: list[str] | None = None
    degree: str | None = None
    graduating_year: int | None = None
    university: str | None = None
    current_location: str | None = None
    summary: str | None = None
    experience_highlights: list[str] | None = None
    projects_summary: list[str] | None = None
    notice_period: str | None = None
    notes: str | None = None


def _serialize(job: dict) -> dict:
    draft = job.get("draft")
    if draft:
        bullets = draft.get("resume_bullets")
        screening = draft.get("screening_answers")
        try:
            draft["resume_bullets"] = json.loads(bullets) if isinstance(bullets, str) else (bullets or [])
        except json.JSONDecodeError:
            draft["resume_bullets"] = []
        try:
            draft["screening_answers"] = json.loads(screening) if isinstance(screening, str) else (screening or {})
        except json.JSONDecodeError:
            draft["screening_answers"] = {}

    score_json = job.get("score_json")
    if isinstance(score_json, str) and score_json:
        try:
            job["score_json"] = json.loads(score_json)
        except json.JSONDecodeError:
            pass

    match_breakdown = job.get("match_breakdown")
    if isinstance(match_breakdown, str) and match_breakdown:
        try:
            job["match_breakdown"] = json.loads(match_breakdown)
        except json.JSONDecodeError:
            pass
    elif not match_breakdown and isinstance(job.get("score_json"), dict):
        job["match_breakdown"] = job["score_json"].get("match_breakdown", {})

    skills_matched = job.get("skills_matched")
    if isinstance(skills_matched, str) and skills_matched:
        try:
            job["skills_matched"] = json.loads(skills_matched)
        except json.JSONDecodeError:
            job["skills_matched"] = []
    elif not skills_matched and isinstance(job.get("score_json"), dict):
        job["skills_matched"] = job["score_json"].get("skills_matched", [])

    if job.get("description"):
        job["description"] = html_to_text(job["description"])

    return job


@app.on_event("startup")
def startup() -> None:
    try:
        init_db()
        backfill_plain_descriptions()
        backfill_metadata()
    except Exception:
        pass


from fastapi import Request


@app.get("/api/debug-headers")
def debug_headers(request: Request) -> dict:
    return {
        "headers": dict(request.headers),
        "url": str(request.url),
        "path": request.url.path,
        "scope_path": request.scope.get("path"),
    }


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "jobcopilot"}


@app.get("/favicon.ico")
@app.head("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/")
@app.head("/")
@app.get("/api/index.py")
@app.head("/api/index.py")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/me")
def api_me() -> dict:
    profile = load_profile()
    p = profile.to_dict()
    headline = f"{p.get('degree') or 'Candidate'} ({p.get('graduating_year') or ''}) · {p.get('target_location') or ''}".strip(" ·")
    return {
        "name": p.get("name") or "",
        "headline": headline,
        "target_location": p.get("target_location") or "",
        "degree": p.get("degree") or "",
        "graduating_year": p.get("graduating_year"),
        "university": p.get("university") or "",
        "open_to": p.get("open_to"),
        "target_domains": p.get("target_domains"),
    }


@app.get("/api/profile")
def api_get_profile() -> dict:
    profile = load_profile()
    return profile.to_dict()


@app.put("/api/profile")
def api_update_profile(body: ProfileUpdate) -> dict:
    profile = load_profile()
    current = profile.to_dict()
    updates = body.dict(exclude_unset=True)
    current.update({k: v for k, v in updates.items() if v is not None})
    save_profile(current)
    return load_profile().to_dict()


@app.get("/api/preferences")
def api_preferences() -> dict:
    profile = load_profile().to_dict()
    md_file = get_resume_path()
    has_existing = md_file.exists() and bool(md_file.read_text(encoding="utf-8").strip())
    return {
        "profile": profile,
        "all_cities": INDIAN_TECH_CITIES,
        "all_domains": AVAILABLE_DOMAINS,
        "has_existing_resume": has_existing,
        "existing_resume_name": "resume.md" if has_existing else None,
    }


@app.put("/api/preferences")
def api_update_preferences(body: ProfileUpdate) -> dict:
    profile = load_profile()
    current = profile.to_dict()
    updates = body.dict(exclude_unset=True)
    current.update({k: v for k, v in updates.items() if v is not None})
    save_profile(current)
    return {
        "profile": load_profile().to_dict(),
        "all_cities": INDIAN_TECH_CITIES,
        "all_domains": AVAILABLE_DOMAINS,
    }


@app.post("/api/resume/upload")
async def api_upload_resume(file: UploadFile = File(...)) -> dict:
    try:
        content = await file.read()
        raw_text = extract_text_from_bytes(content, file.filename or "resume.pdf")
        parsed = parse_resume_text(raw_text)
        return {
            "status": "success",
            "filename": file.filename,
            "parsed": parsed,
            "raw_text": raw_text,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")


@app.post("/api/resume/scan-existing")
def api_scan_existing_resume() -> dict:
    md_path = get_resume_path()
    if md_path.exists() and md_path.read_text(encoding="utf-8").strip():
        raw_text = md_path.read_text(encoding="utf-8", errors="ignore")
        parsed = parse_resume_text(raw_text)
        return {
            "status": "success",
            "filename": "resume.md",
            "parsed": parsed,
            "raw_text": raw_text,
        }
    raise HTTPException(status_code=404, detail="No existing resume file found on disk.")


@app.post("/api/resume/scan-text")
def api_scan_text_resume(body: TextScanIn) -> dict:
    parsed = parse_resume_text(body.text)
    return {
        "status": "success",
        "filename": "pasted_text.txt",
        "parsed": parsed,
        "raw_text": body.text,
    }


@app.get("/api/ai/status")
def api_ai_status() -> dict:
    return get_ai_status()


@app.post("/api/resume/save")
def api_save_parsed_resume(body: ResumeSaveIn) -> dict:
    updated = save_parsed_profile(body.parsed, body.raw_text)
    rescored = 0
    if body.rescore:
        rescored = rescore_all_jobs()
    sync_result = None
    if body.trigger_sync:
        sync_result = trigger_sync_now(background=True)
    return {
        "status": "saved",
        "profile": updated,
        "rescored": rescored,
        "sync_result": sync_result,
    }


@app.post("/api/profile/reset")
def api_reset_profile() -> dict:
    from jobcopilot.profile import reset_to_clean_profile
    clean = reset_to_clean_profile()
    with connect() as conn:
        conn.execute("DELETE FROM drafts")
        conn.commit()
    return {
        "status": "reset",
        "profile": clean,
    }


@app.get("/api/autosync")
def api_get_autosync() -> dict:
    return get_autosync_status()


@app.post("/api/autosync/toggle")
def api_toggle_autosync(body: AutoSyncToggleIn) -> dict:
    return set_autosync_enabled(body.enabled, body.interval_minutes)


@app.post("/api/autosync/trigger")
def api_trigger_autosync() -> dict:
    return trigger_sync_now()


@app.get("/api/filters")
def api_filters() -> dict:
    with connect() as conn:
        return get_available_filters(conn)


@app.get("/api/stats")
def api_stats() -> dict:
    with connect() as conn:
        return counts(conn)


@app.get("/api/jobs")
def api_jobs(
    status: str | None = None,
    city: str | None = None,
    domain: str | None = None,
    search: str | None = None,
    min_score: int | None = None,
) -> list[dict]:
    with connect() as conn:
        return [_serialize(j) for j in list_jobs(conn, status=status, city=city, domain=domain, search=search, min_score=min_score)]


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


@app.post("/api/rescore")
def api_rescore() -> dict:
    return rescore_all_jobs()


@app.post("/api/jobs/{job_id}/rescore")
def api_rescore_job(job_id: int) -> dict:
    job = rescore_single_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _serialize(job)


@app.post("/api/jobs/{job_id}/generate-ai")
def api_generate_ai_job(job_id: int) -> dict:
    job = rescore_single_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _serialize(job)


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
        conn.commit()
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.post("/api/jobs/{job_id}/approve")
def api_approve(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        set_status(conn, job_id, "ready")
        conn.commit()
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
        conn.commit()
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.post("/api/jobs/{job_id}/skip")
def api_skip(job_id: int) -> dict:
    with connect() as conn:
        job = get_job(conn, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        set_status(conn, job_id, "skipped")
        conn.commit()
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
        conn.commit()
        job = get_job(conn, job_id)
    return _serialize(job or {})


@app.get("/api/export")
def api_export(status: str | None = None, format: str = "csv") -> Response:
    with connect() as conn:
        content = export_jobs_data(conn, status=status, fmt=format)
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"jobcopilot_export_{status or 'all'}.{format}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/open/{job_id}")
def open_job(job_id: int) -> RedirectResponse:
    with connect() as conn:
        job = get_job(conn, job_id)
    if not job or not job.get("url"):
        raise HTTPException(404, "No apply URL")
    return RedirectResponse(job["url"])


def create_app() -> FastAPI:
    return app
