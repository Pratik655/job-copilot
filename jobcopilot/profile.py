from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jobcopilot.settings import ROOT


@dataclass
class Profile:
    name: str
    target_location: str
    open_to: list[str]
    target_titles: list[str]
    years_experience: int
    stack: list[str]
    must_have: list[str]
    nice_to_have: list[str]
    deal_breakers: list[str]
    notice_period: str
    current_location: str
    ctc_expectation: str
    work_authorization: str
    salary_band: str
    notes: str
    resume: str
    email: str = ""
    phone: str = ""
    degree: str = ""
    graduating_year: int = 2026
    university: str = ""
    target_domains: list[str] = field(default_factory=list)
    max_experience_allowed: int = 2
    summary: str = ""
    experience_highlights: list[str] = field(default_factory=list)
    projects_summary: list[str] = field(default_factory=list)

    def as_prompt_block(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"Email: {self.email}\n"
            f"Phone: {self.phone}\n"
            f"Location: {self.current_location}\n"
            f"Degree: {self.degree} ({self.graduating_year} Batch)\n"
            f"University: {self.university}\n"
            f"Target location: {self.target_location}\n"
            f"Open to locations: {', '.join(self.open_to)}\n"
            f"Target domains: {', '.join(self.target_domains) or 'Software Development, Web, Data & AI, Cloud, QA'}\n"
            f"Target titles: {', '.join(self.target_titles)}\n"
            f"Years of Experience: {self.years_experience} (Fresher graduating in {self.graduating_year})\n"
            f"Tech Stack: {', '.join(self.stack)}\n"
            f"Professional Summary: {self.summary}\n"
            f"Experience Highlights: {'; '.join(self.experience_highlights)}\n"
            f"Must have: {', '.join(self.must_have) or 'none'}\n"
            f"Nice to have: {', '.join(self.nice_to_have) or 'none'}\n"
            f"Deal breakers: {', '.join(self.deal_breakers) or 'none'}\n"
            f"Notice period: {self.notice_period}\n"
            f"Current location: {self.current_location}\n"
            f"CTC: {self.ctc_expectation}\n"
            f"Work auth: {self.work_authorization}\n"
            f"Notes: {self.notes}\n\n"
            f"Resume:\n{self.resume}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "degree": self.degree,
            "graduating_year": self.graduating_year,
            "university": self.university,
            "target_location": self.target_location,
            "current_location": self.current_location,
            "open_to": self.open_to,
            "target_domains": self.target_domains,
            "target_titles": self.target_titles,
            "years_experience": self.years_experience,
            "max_experience_allowed": self.max_experience_allowed,
            "stack": self.stack,
            "summary": self.summary,
            "experience_highlights": self.experience_highlights,
            "projects_summary": self.projects_summary,
            "must_have": self.must_have,
            "nice_to_have": self.nice_to_have,
            "deal_breakers": self.deal_breakers,
            "notice_period": self.notice_period,
            "ctc_expectation": self.ctc_expectation,
            "work_authorization": self.work_authorization,
            "salary_band": self.salary_band,
            "notes": self.notes,
            "resume": self.resume,
        }


from jobcopilot.paths import get_profile_path, get_resume_path
from jobcopilot.settings import ROOT


def load_profile(
    profile_path: Path | None = None, resume_path: Path | None = None
) -> Profile:
    profile_path = profile_path or get_profile_path()
    resume_path = resume_path or get_resume_path()
    data = {}
    if profile_path.exists():
        data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    resume = resume_path.read_text(encoding="utf-8") if resume_path.exists() else ""

    # If resume exists, auto-enrich any empty contact or summary fields
    if resume.strip():
        try:
            from jobcopilot.resume_parser import parse_resume_text
            parsed = parse_resume_text(resume)
            if not data.get("name") and parsed.get("name"):
                data["name"] = parsed["name"]
            if not data.get("email") and parsed.get("email"):
                data["email"] = parsed["email"]
            if not data.get("phone") and parsed.get("phone"):
                data["phone"] = parsed["phone"]
            if not data.get("degree") and parsed.get("degree"):
                data["degree"] = parsed["degree"]
            if not data.get("university") and parsed.get("university"):
                data["university"] = parsed["university"]
            if not data.get("current_location") and parsed.get("current_location"):
                data["current_location"] = parsed["current_location"]
            if not data.get("summary") and parsed.get("summary"):
                data["summary"] = parsed["summary"]
            if not data.get("experience_highlights") and parsed.get("experience_highlights"):
                data["experience_highlights"] = parsed["experience_highlights"]
            if not data.get("projects_summary") and parsed.get("projects_summary"):
                data["projects_summary"] = parsed["projects_summary"]
            if not data.get("stack") and parsed.get("skills"):
                data["stack"] = parsed["skills"]
        except Exception:
            pass

    return Profile(
        name=str(data.get("name") or ""),
        email=str(data.get("email") or ""),
        phone=str(data.get("phone") or ""),
        degree=str(data.get("degree") or ""),
        graduating_year=int(data.get("graduating_year") or 2026),
        university=str(data.get("university") or ""),
        target_location=str(data.get("target_location", "")),
        current_location=str(data.get("current_location", "")),
        open_to=list(data.get("open_to") or [
            "Bangalore", "Hyderabad", "Pune", "Delhi-NCR", "Mumbai",
            "Chennai", "Kolkata", "Ahmedabad", "Remote India"
        ]),
        target_domains=list(data.get("target_domains") or ["tech", "data", "trainee_campus"]),
        target_titles=list(data.get("target_titles") or [
            "Software Engineer", "SDE-1", "Full Stack Developer", "Python Developer", "Data Analyst"
        ]),
        years_experience=int(data.get("years_experience") or 0),
        max_experience_allowed=int(data.get("max_experience_allowed") or 2),
        stack=list(data.get("stack") or []),
        summary=str(data.get("summary") or ""),
        experience_highlights=list(data.get("experience_highlights") or []),
        projects_summary=list(data.get("projects_summary") or []),
        must_have=list(data.get("must_have") or []),
        nice_to_have=list(data.get("nice_to_have") or []),
        deal_breakers=list(data.get("deal_breakers") or []),
        notice_period=str(data.get("notice_period", "Immediate")),
        ctc_expectation=str(data.get("ctc_expectation", "")),
        work_authorization=str(data.get("work_authorization", "")),
        salary_band=str(data.get("salary_band", "")),
        notes=str(data.get("notes", "")),
        resume=resume,
    )


def save_profile(data: dict[str, Any], profile_path: Path | None = None) -> None:
    profile_path = profile_path or get_profile_path()
    content = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    try:
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(content, encoding="utf-8")
    except OSError:
        tmp_path = Path("/tmp") / "profile.yaml"
        tmp_path.write_text(content, encoding="utf-8")


def reset_to_clean_profile(profile_path: Path | None = None, resume_path: Path | None = None) -> dict[str, Any]:
    """Completely wipe out all candidate data, returning workspace to a blank slate."""
    profile_path = profile_path or get_profile_path()
    resume_path = resume_path or get_resume_path()
    clean_data = {
        "name": "",
        "email": "",
        "phone": "",
        "degree": "",
        "graduating_year": 2026,
        "university": "",
        "target_location": "",
        "current_location": "",
        "open_to": [
            "Bangalore", "Hyderabad", "Pune", "Delhi-NCR", "Mumbai",
            "Chennai", "Kolkata", "Ahmedabad", "Remote India"
        ],
        "target_domains": ["tech", "data", "trainee_campus"],
        "target_titles": [
            "Software Engineer", "SDE-1", "Full Stack Developer", "Python Developer", "Data Analyst"
        ],
        "years_experience": 0,
        "max_experience_allowed": 2,
        "stack": [],
        "summary": "",
        "experience_highlights": [],
        "projects_summary": [],
        "must_have": [],
        "nice_to_have": [],
        "deal_breakers": [],
        "notice_period": "Immediate",
        "ctc_expectation": "Open to discuss for entry-level / fresher roles",
        "work_authorization": "Authorized to work in India",
        "salary_band": "",
        "notes": "",
        "resume": "",
    }
    save_profile(clean_data, profile_path=profile_path)
    if resume_path.exists():
        try:
            resume_path.write_text("", encoding="utf-8")
        except OSError:
            pass
    return clean_data
