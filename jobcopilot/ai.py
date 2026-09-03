from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

from jobcopilot import QUEUE_THRESHOLD, ROOT
from jobcopilot.profile import load_profile

load_dotenv(ROOT / ".env")


def _heuristic(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    blob = f"{job.get('title', '')} {job.get('location', '')} {job.get('description', '')}".lower()
    stacks = [s.lower() for s in profile.get("stacks") or []]
    hits = [s for s in stacks if s and s in blob]
    title_hit = any(t.lower() in (job.get("title") or "").lower() for t in profile.get("target_titles") or [])
    loc = (job.get("location") or "").lower()
    loc_hit = any(x in loc for x in ("bangalore", "bengaluru", "india", "remote", "hybrid"))
    score = min(100, 20 + 10 * len(hits) + (15 if title_hit else 0) + (15 if loc_hit else 0))
    why = []
    if hits:
        why.append("Stack overlap: " + ", ".join(hits[:8]))
    if title_hit:
        why.append("Title matches your target roles.")
    if loc_hit:
        why.append("Location looks compatible with Bangalore / India / remote.")
    if not why:
        why.append("Weak overlap with your profile; review before applying.")
    name = profile.get("name") or "I"
    company = job.get("company") or "your team"
    title = job.get("title") or "this role"
    cover = (
        f"Hi,\n\nI'm {name}, a software engineer based in Bangalore. I'm interested in the "
        f"{title} role at {company}. My background covers {', '.join((profile.get('stacks') or [])[:5]) or 'backend and product engineering'}. "
        f"I'd welcome a conversation about how I can contribute.\n\nThanks,\n{name}\n"
    )
    bullets = [
        f"Shipped production software overlapping {hits[0]}." if hits else "Shipped production software end to end.",
        "Owned reliability, code review, and delivery on a customer-facing service.",
        "Collaborated with product to scope and ship iterative releases.",
    ]
    screening = {
        "notice_period": profile.get("notice_period") or "",
        "location": profile.get("target_location") or "Bangalore",
        "salary_band": profile.get("salary_band") or "",
    }
    referral = (
        f"Hi — I'm {name}, looking at {title} at {company} in Bangalore. "
        f"If you're open to a referral or a quick intro, I can send a resume. Thanks."
    )
    decision = "queue" if score >= QUEUE_THRESHOLD else "skip"
    return {
        "score": score,
        "decision": decision,
        "why_apply": " ".join(why) if decision == "queue" else "",
        "why_skip": "" if decision == "queue" else " ".join(why),
        "cover_letter": cover,
        "resume_bullets": bullets,
        "screening_answers": screening,
        "referral_message": referral,
        "mode": "heuristic",
    }


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    return json.loads(text)


def _task_prompt(job: dict[str, Any], profile: dict[str, Any]) -> str:
    return (
        "Score this software-engineer job for a candidate hunting in Bangalore. "
        "Do not browse the web, scrape sites, or apply. Use only the profile, resume, and job text below. "
        "Return ONLY JSON with keys: score (0-100 integer), decision (queue|skip), "
        "why_apply, why_skip, cover_letter, resume_bullets (array of 3-6 strings), "
        "screening_answers (object with notice_period, location, salary_band), referral_message. "
        "Tailor cover_letter and bullets to the JD using only facts from the resume and profile. "
        "When relevant, cite Ford EV-charging metrics and/or TripBeacon (Go core, NestJS, React Native). "
        "Do not invent employers or metrics.\n\n"
        f"PROFILE:\n{json.dumps({k: profile[k] for k in profile if k != 'resume'}, indent=2)}\n\n"
        f"RESUME:\n{profile.get('resume', '')[:8000]}\n\n"
        f"JOB:\n{json.dumps({k: job.get(k) for k in ('company', 'title', 'location', 'url', 'description')}, indent=2)[:12000]}"
    )


def _normalize(data: dict[str, Any], mode: str) -> dict[str, Any]:
    data = dict(data)
    data["mode"] = mode
    data["score"] = int(data.get("score") or 0)
    if data["score"] < QUEUE_THRESHOLD:
        data["decision"] = "skip"
    elif data.get("decision") not in {"queue", "skip"}:
        data["decision"] = "queue"
    return data


def _result_text(result: Any) -> str:
    payload = getattr(result, "result", result)
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("text", "message", "content"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        return json.dumps(payload)
    return str(payload)


def _cursor_model():
    from cursor_sdk.types import ModelParameterValue, ModelSelection

    model_id = os.getenv("CURSOR_MODEL", "composer-2.5").strip() or "composer-2.5"
    params = [ModelParameterValue(id="fast", value="false")]
    if model_id.startswith("grok"):
        params.insert(0, ModelParameterValue(id="effort", value="medium"))
    return ModelSelection(id=model_id, params=tuple(params))


def _cursor(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
    except ImportError:
        return None
    try:
        result = Agent.prompt(
            _task_prompt(job, profile),
            AgentOptions(
                api_key=api_key,
                model=_cursor_model(),
                local=LocalAgentOptions(cwd=str(ROOT)),
            ),
        )
    except CursorAgentError as exc:
        print(f"Cursor agent failed to start: {exc}", flush=True)
        return None
    if getattr(result, "status", None) != "finished":
        print(f"Cursor run status={getattr(result, 'status', None)}", flush=True)
        return None
    try:
        return _normalize(_extract_json(_result_text(result)), "cursor")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Cursor returned non-JSON: {exc}", flush=True)
        return None


def _openai(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "You help a job seeker prepare applications. Never submit anything."},
                        {"role": "user", "content": _task_prompt(job, profile)},
                    ],
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _normalize(_extract_json(content), "openai")
    except Exception:
        return None


def score_and_draft(job: dict[str, Any], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = profile or load_profile()
    return _cursor(job, profile) or _openai(job, profile) or _heuristic(job, profile)
