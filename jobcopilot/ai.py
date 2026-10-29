from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

from jobcopilot import QUEUE_THRESHOLD, ROOT
from jobcopilot.filters import (
    check_btech_cse_eligibility,
    detect_domain,
    detect_experience_level,
    is_location_relevant,
    is_senior_or_experienced,
    normalize_city,
)
from jobcopilot.profile import load_profile

load_dotenv(ROOT / ".env")


def _heuristic(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    title = (job.get("title") or "").strip()
    company = (job.get("company") or "Team").strip()
    loc = (job.get("location") or "").strip()
    desc = (job.get("description") or "").strip()
    blob = f"{title} {loc} {desc}".lower()

    name = profile.get("name") or "Candidate"
    degree = profile.get("degree") or "Degree"
    grad_year = profile.get("graduating_year") or ""
    university = profile.get("university") or ""
    normalized_city_name = normalize_city(loc, desc)
    dom_key, dom_label = detect_domain(title, desc)
    exp_level = detect_experience_level(title, desc)
    btech_info = check_btech_cse_eligibility(title, desc)

    uni_detail = f", {university}" if university else ""
    batch_detail = f" ({grad_year} Batch{uni_detail})" if grad_year else (f" ({university})" if university else "")
    screening = {
        "notice_period": profile.get("notice_period") or "Immediate",
        "location": f"Ready to relocate to {normalized_city_name} or Remote India",
        "degree": f"{degree}{batch_detail}".strip(),
        "salary_band": profile.get("salary_band") or "Open for entry-level / fresher roles",
        "work_authorization": "Indian citizen, authorized to work in India",
    }

    # Helper to generate tailored packets using the candidate's real resume profile
    def _generate_packets(hits: list[str], domain_key: str) -> tuple[str, list[str], str]:
        hit_str = ", ".join(hits[:5]) if hits else ", ".join(profile.get("stack", [])[:5]) or "problem solving, analytics, and project execution"

        candidate_summary = (profile.get("summary") or "").strip()
        candidate_exp = profile.get("experience_highlights") or []
        candidate_proj = profile.get("projects_summary") or []
        candidate_stack = profile.get("stack") or []

        # 1. Build Hook / Narrative from candidate's real resume data
        if candidate_summary:
            if candidate_exp and candidate_exp[0] not in candidate_summary:
                hook = f"{candidate_summary}\n\nMy practical background includes hands-on experience in {candidate_exp[0]}."
            else:
                hook = candidate_summary
        elif candidate_exp:
            exp_text = "; ".join(candidate_exp[:2])
            hook = f"My hands-on background includes {exp_text}. I bring a strong foundation in {hit_str} with a focus on delivering reliable, high-quality results."
        elif domain_key == "marketing":
            hook = (
                f"I bring a data-driven, analytical mindset to marketing and growth. "
                f"With hands-on experience in data analysis and digital applications, "
                f"I excel at interpreting audience trends, creating engaging digital content, and optimizing marketing campaigns."
            )
        elif domain_key == "sales_bd":
            hook = (
                f"I combine strong interpersonal communication with fast learning and high energy. "
                f"I can grasp products quickly and articulate business value clearly to prospective clients, "
                f"making me well-suited for business development, sales, and client-facing roles."
            )
        elif domain_key in ("product_ops", "consulting_biz"):
            hook = (
                f"I combine analytical thinking with operational rigor and problem solving. "
                f"I enjoy bridging the gap between business goals, customer needs, and execution "
                f"to drive smooth operations and impactful project workflows."
            )
        elif domain_key == "data":
            hook = (
                f"My background centers on data analytics, quantitative workflows, and problem solving, "
                f"cleaning datasets and extracting actionable business metrics."
            )
        else:
            hook = (
                f"My technical background centers on {hit_str}, aligning directly with your requirements for {title}. "
                f"I focus on clean architecture, practical problem solving, and disciplined development workflows."
            )

        # 2. Build Bullets from candidate's real resume
        bullets = []
        if candidate_exp:
            for exp_item in candidate_exp[:2]:
                bullets.append(exp_item)
        if candidate_proj:
            for proj_item in candidate_proj[:2]:
                bullets.append(proj_item)

        fallback_bullets = [
            f"Hands-on competency in {hit_str}, applied toward building reliable solutions.",
            f"Strong structured problem solving and fast learning ability, adapting rapidly to new tools and environments.",
            f"Proactive communicator and collaborative team player with disciplined version control and project organization.",
            f"Eager to contribute immediately to {company}'s roadmap and team targets.",
        ]
        for fb in fallback_bullets:
            if len(bullets) >= 4:
                break
            if fb not in bullets:
                bullets.append(fb)

        # 3. Referral Message
        referral = (
            f"Hi — I'm {name}, an enthusiastic applicant interested in the {title} role at {company}. "
            f"I have hands-on experience in {hit_str}. Would love to connect! Thanks!"
        )

        uni_str = f" from {university}" if university else ""
        year_str = f" graduating in {grad_year}" if grad_year else ""
        deg_str = f", a {degree}{year_str}{uni_str}" if degree else (f"{uni_str}" if university else "")
        email = profile.get("email") or ""
        phone = profile.get("phone") or ""
        location_candidate = profile.get("current_location") or normalized_city_name

        contacts = []
        if email:
            contacts.append(f"Email: {email}")
        if phone:
            contacts.append(f"Phone: {phone}")
        if location_candidate:
            contacts.append(f"Location: {location_candidate}")
        contacts_footer = ("\n" + " | ".join(contacts)) if contacts else ""

        cover = (
            f"Dear {company} Hiring Team,\n\n"
            f"I am {name}{deg_str}, "
            f"actively applying for the {title} position at {company}.\n\n"
            f"{hook}\n\n"
            f"In this role, I focus on delivering quality execution in {hit_str}. "
            f"I am adaptable, fast at learning new technologies, and passionate about creating tangible impact for {company}. "
            f"I welcome the opportunity to discuss how my skill set and enthusiasm align with your team's goals.\n\n"
            f"Thank you for your time and consideration,\n\n"
            f"Sincerely,\n{name}{contacts_footer}\n"
        )
        return cover, bullets, referral

    # ==========================================================================
    # SENIORITY CHECK (Only exclude actual senior/lead/director roles)
    # ==========================================================================
    if is_senior_or_experienced(title, desc) or btech_info.get("too_experienced"):
        cover, bullets, referral = _generate_packets([], dom_key)
        return {
            "score": 15,
            "decision": "skip",
            "why_apply": "",
            "why_skip": "Role requires senior/lead level (>2 years exp); candidate is a 2026 graduate.",
            "cover_letter": cover,
            "resume_bullets": bullets,
            "screening_answers": screening,
            "referral_message": referral,
            "match_breakdown": {
                "degree_fit": {"score": 10, "max": 25, "status": "Senior Level", "detail": "Requires senior experience"},
                "role_fit": {"score": 5, "max": 25, "status": "Too Senior", "detail": "Senior/Staff level"},
                "skills_fit": {"score": 0, "max": 30, "status": "Skipped", "detail": "Not evaluated"},
                "location_fit": {"score": 0, "max": 20, "status": "Skipped", "detail": normalized_city_name},
                "fresher_friendly": False,
            },
            "skills_matched": [],
            "mode": "heuristic",
        }

    # ==========================================================================
    # LOCATION CHECK (Must be India or Remote)
    # ==========================================================================
    if not is_location_relevant(loc, desc):
        cover, bullets, referral = _generate_packets([], dom_key)
        return {
            "score": 10,
            "decision": "skip",
            "why_apply": "",
            "why_skip": f"Location ({loc or 'unspecified'}) is outside supported Indian tech hubs or Remote India.",
            "cover_letter": cover,
            "resume_bullets": bullets,
            "screening_answers": screening,
            "referral_message": referral,
            "match_breakdown": {
                "degree_fit": {"score": 15, "max": 25, "status": "Eligible", "detail": "Eligible profile"},
                "role_fit": {"score": 15, "max": 25, "status": "Eligible", "detail": title},
                "skills_fit": {"score": 0, "max": 30, "status": "Skipped", "detail": "Not evaluated"},
                "location_fit": {"score": 0, "max": 20, "status": "Excluded", "detail": "Foreign location"},
                "fresher_friendly": btech_info.get("is_fresher_friendly", False),
            },
            "skills_matched": [],
            "mode": "heuristic",
        }

    # ==========================================================================
    # SCORING ENGINE (Open to all Graduate & Early Career Roles)
    # ==========================================================================

    # 1. Degree & Educational Foundation (Max 25)
    degree_score = 22
    degree_status = "Graduate Eligible"
    degree_detail = "Matches 2026 graduate profile"
    if btech_info.get("degree_matched"):
        degree_score = 25
        degree_status = "Exact Match"
        degree_detail = f"JD mentions graduate/degree requirements"
    elif btech_info.get("is_fresher_friendly"):
        degree_score = 24
        degree_status = "Fresher Friendly"
        degree_detail = "Explicitly welcomes freshers & early career"

    # 2. Role & Seniority Fit (Max 25)
    role_score = 20
    role_status = "Entry Level"
    role_detail = f"{exp_level} role in {dom_label}"
    if any(k in title.lower() for k in ("intern", "trainee", "associate", "graduate", "junior", "entry level", "fresher", "get", "sde-1", "sde 1", "assistant", "executive")):
        role_score = 25
        role_status = "Ideal Entry Role"
        role_detail = f"Ideal graduate entry point: {title}"

    # 3. Skills & Versatility Overlap (Max 30)
    skill_keywords = {
        "node": "Node.js", "mongodb": "MongoDB", "python": "Python", "javascript": "JavaScript",
        "react": "React", "html": "HTML5", "css": "CSS3", "git": "Git", "sql": "SQL",
        "data analysis": "Data Analysis", "analytics": "Analytics", "marketing": "Marketing",
        "sales": "Sales & BD", "communication": "Communication", "problem solving": "Problem Solving",
        "operations": "Operations", "excel": "Excel / Sheets", "research": "Market Research",
        "content": "Content & Media", "seo": "SEO & Growth",
    }
    matched_skills = []
    seen = set()
    for kw, label in skill_keywords.items():
        if kw in blob:
            if label not in seen:
                seen.add(label)
                matched_skills.append(label)

    skills_score = min(30, max(15, len(matched_skills) * 6))

    # 4. Location Fit (Max 20)
    loc_score = 18
    norm_lower = normalized_city_name.lower()
    if "bangalore" in norm_lower or "bengaluru" in norm_lower:
        loc_score = 20
        loc_status = "Target Location"
    elif "remote" in norm_lower:
        loc_score = 20
        loc_status = "Remote India"
    else:
        loc_score = 18
        loc_status = normalized_city_name

    total_score = min(100, max(0, degree_score + role_score + skills_score + loc_score))
    decision = "queue" if total_score >= 50 else "skip"

    why_apply = f"Great fit for {dom_label} ({exp_level}). Location: {normalized_city_name}."
    if matched_skills:
        why_apply += f" Overlap with: {', '.join(matched_skills[:4])}."

    cover, bullets, referral = _generate_packets(matched_skills, dom_key)

    match_breakdown = {
        "degree_fit": {"score": degree_score, "max": 25, "status": degree_status, "detail": degree_detail},
        "role_fit": {"score": role_score, "max": 25, "status": role_status, "detail": role_detail},
        "skills_fit": {
            "score": skills_score,
            "max": 30,
            "status": "Good" if skills_score >= 20 else "Basic",
            "detail": f"{len(matched_skills)} competencies aligned",
        },
        "location_fit": {"score": loc_score, "max": 20, "status": loc_status, "detail": normalized_city_name},
        "domain": dom_label,
        "experience_level": exp_level,
        "city": normalized_city_name,
        "fresher_friendly": btech_info.get("is_fresher_friendly", False),
    }

    return {
        "score": total_score,
        "decision": decision,
        "why_apply": why_apply if decision == "queue" else "",
        "why_skip": f"Score {total_score} below queue threshold (50)." if decision == "skip" else "",
        "cover_letter": cover,
        "resume_bullets": bullets,
        "screening_answers": screening,
        "referral_message": referral,
        "match_breakdown": match_breakdown,
        "skills_matched": matched_skills,
        "mode": "heuristic",
    }


import collections
import time
import threading


class ApinexRateLimiter:
    """Strictly enforces 5 requests per 60 seconds (1min me 5 req limit)."""

    def __init__(self, max_requests: int = 5, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: collections.deque[float] = collections.deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.time()
            # Prune timestamps older than window
            while self.timestamps and (now - self.timestamps[0]) >= self.window_seconds:
                self.timestamps.popleft()

            # If 5 requests already happened in the last 60s, wait until slot frees up
            if len(self.timestamps) >= self.max_requests:
                sleep_needed = self.window_seconds - (now - self.timestamps[0]) + 0.5
                if sleep_needed > 0:
                    time.sleep(sleep_needed)
                    now = time.time()
                    while self.timestamps and (now - self.timestamps[0]) >= self.window_seconds:
                        self.timestamps.popleft()

            # Ensure minimum spacing between consecutive calls (12s)
            min_gap = self.window_seconds / self.max_requests
            if self.timestamps:
                gap = now - self.timestamps[-1]
                if gap < min_gap:
                    time.sleep(min_gap - gap)
                    now = time.time()

            self.timestamps.append(time.time())


_apinex_limiter = ApinexRateLimiter(max_requests=5, window_seconds=60.0)


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {}


def _task_prompt(job: dict[str, Any], profile: dict[str, Any]) -> str:
    candidate_name = profile.get("name") or "the Candidate"
    grad_year = profile.get("graduating_year") or "Recent Graduate"
    return (
        f"You are an AI Career Copilot evaluating early-career & graduate jobs in India for candidate {candidate_name} ({grad_year}).\n"
        "The candidate is open to early-career positions across:\n"
        "- Tech & Software Engineering (SDE-1, Web, Backend, QA, Cloud)\n"
        "- Data Science & Analytics\n"
        "- Digital Marketing, Growth & Content\n"
        "- Business Development, Sales & Customer Success\n"
        "- Product & Operations\n"
        "- Management Trainee & Graduate Trainee\n\n"
        "Rules:\n"
        "1. Strictly skip (>2 years required, senior, lead, manager, director) with score <30.\n"
        "2. Queue early career/graduate/fresher roles in Indian cities or Remote India.\n"
        "3. Return ONLY valid JSON with keys: score (0-100), decision (queue|skip), why_apply, why_skip, cover_letter, resume_bullets, screening_answers, referral_message, skills_matched.\n\n"
        f"PROFILE:\n{json.dumps({k: profile[k] for k in profile if k != 'resume'}, indent=2)}\n\n"        f"CANDIDATE RESUME / BACKGROUND:\n{str(profile.get('resume', ''))[:3000]}\n\n"
        f"JOB:\n{json.dumps({k: job.get(k) for k in ('company', 'title', 'location', 'url', 'description')}, indent=2)[:10000]}"
    )


def _normalize(data: dict[str, Any], mode: str, job: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(data)
    data["mode"] = mode
    data["score"] = int(data.get("score") or 0)
    if data["score"] < 50:
        data["decision"] = "skip"
    elif data.get("decision") not in {"queue", "skip"}:
        data["decision"] = "queue"
    return data


RADOX_DEFAULT_KEY = "cc_5uzsNgoInTAWPhm2wOr1uDxJcRRMvfsCwGKD9O8CMQSO7xWk"
RADOX_DEFAULT_URL = "https://radoxai.com/v1"
RADOX_DEFAULT_MODEL = "gpt-5.6-luna"

# Multi-model fallback cascade in priority order
RADOX_MODEL_CASCADE = [
    "gpt-5.6-luna",
    "gemini-3.7-flash",
    "gpt-5.6-terra",
    "kimi-k3",
    "deepseek-v4-flash-0731",
    "gpt-5.5",
]

_cached_models: list[str] = []
_active_model: str = RADOX_DEFAULT_MODEL


def fetch_available_models() -> list[str]:
    global _cached_models
    if _cached_models:
        return list(_cached_models)
    key = os.getenv("RADOX_API_KEY") or os.getenv("OPENAI_API_KEY") or RADOX_DEFAULT_KEY
    base = (os.getenv("RADOX_BASE_URL") or os.getenv("OPENAI_BASE_URL") or RADOX_DEFAULT_URL).rstrip("/")
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                _cached_models = [m.get("id") for m in items if isinstance(m, dict) and m.get("id")]
                return list(_cached_models)
    except Exception:
        pass
    return list(RADOX_MODEL_CASCADE)


def get_ai_status() -> dict[str, Any]:
    global _active_model
    models = fetch_available_models()
    key = os.getenv("RADOX_API_KEY") or os.getenv("OPENAI_API_KEY") or RADOX_DEFAULT_KEY
    base = (os.getenv("RADOX_BASE_URL") or os.getenv("OPENAI_BASE_URL") or RADOX_DEFAULT_URL).rstrip("/")
    return {
        "provider": "Radox AI",
        "base_url": base,
        "active_model": _active_model,
        "available_models_count": len(models),
        "fallback_cascade": RADOX_MODEL_CASCADE,
        "is_configured": bool(key),
    }


def _radox(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any] | None:
    global _active_model
    key = (
        os.getenv("RADOX_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or RADOX_DEFAULT_KEY
    ).strip()
    if not key:
        return None
    base = (
        os.getenv("RADOX_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or RADOX_DEFAULT_URL
    ).rstrip("/")

    preferred_model = (
        os.getenv("RADOX_MODEL")
        or os.getenv("OPENAI_MODEL")
        or RADOX_DEFAULT_MODEL
    ).strip()

    candidate_models = [preferred_model] + [m for m in RADOX_MODEL_CASCADE if m != preferred_model]
    prompt = _task_prompt(job, profile)

    for model in candidate_models:
        for attempt in range(2):
            try:
                with httpx.Client(timeout=35.0) as client:
                    resp = client.post(
                        f"{base}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "temperature": 0.2,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are an AI Career Copilot evaluating early-career & graduate jobs in India. "
                                        "Output strictly valid JSON only with keys: score, decision, why_apply, why_skip, "
                                        "cover_letter, resume_bullets, screening_answers, referral_message, skills_matched."
                                    ),
                                },
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": 2500,
                        },
                    )
                    if resp.status_code == 429:
                        time.sleep(2.0)
                        continue
                    if resp.status_code != 200:
                        break
                    data = resp.json()
                    choices = data.get("choices") or []
                    if not choices:
                        break
                    content = choices[0].get("message", {}).get("content") or ""
                    parsed = _extract_json(content)
                    if parsed and "score" in parsed:
                        _active_model = model
                        return _normalize(parsed, f"radox ({model})", job)
            except Exception:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                break
    return None


def _apinex(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any] | None:
    api_key = (
        os.getenv("APINEX_API_KEY")
        or ""
    ).strip()
    if not api_key:
        return None
    model = (
        os.getenv("APINEX_MODEL")
        or "free/gpt-6-luna"
    ).strip()
    base = (
        os.getenv("APINEX_BASE_URL")
        or "https://api.apinex.bond/v1"
    ).rstrip("/")

    # Strict rate limit: max 5 requests per 60 seconds
    _apinex_limiter.acquire()

    prompt = _task_prompt(job, profile)
    for attempt in range(2):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 0.2,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI Career Copilot evaluating jobs in India. Output strictly valid JSON only with keys: score, decision, why_apply, why_skip, cover_letter, resume_bullets, screening_answers, referral_message, skills_matched.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 3000,
                    },
                )
                if resp.status_code == 429:
                    time.sleep(15.0)
                    continue
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"].get("content") or ""
                parsed = _extract_json(content)
                if parsed and "score" in parsed:
                    return _normalize(parsed, "apinex", job)
        except Exception:
            if attempt == 0:
                time.sleep(5.0)
                continue
            return None
    return None


def _openai(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-apx") or "radoxai" in os.getenv("OPENAI_BASE_URL", ""):
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "You evaluate graduate jobs in India. Never submit anything."},
                        {"role": "user", "content": _task_prompt(job, profile)},
                    ],
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _normalize(_extract_json(content), "openai", job)
    except Exception:
        return None


def score_and_draft(job: dict[str, Any], profile: Any = None) -> dict[str, Any]:
    if profile is None:
        profile = load_profile()
    if is_dataclass(profile):
        p_dict = asdict(profile)
    elif isinstance(profile, dict):
        p_dict = dict(profile)
    elif hasattr(profile, "__dict__"):
        p_dict = vars(profile)
    else:
        p_dict = {}

    if "stack" in p_dict and "stacks" not in p_dict:
        p_dict["stacks"] = p_dict["stack"]
    elif "stacks" in p_dict and "stack" not in p_dict:
        p_dict["stack"] = p_dict["stacks"]

    # Primary: Radox AI (gpt-5.6-luna with full fallback cascade)
    # Secondary: Native OpenAI or Apinex
    # Final fallback: Local heuristic scoring engine
    return _radox(job, p_dict) or _openai(job, p_dict) or _apinex(job, p_dict) or _heuristic(job, p_dict)
