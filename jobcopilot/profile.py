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
    degree: str = ""
    graduating_year: int = 2026
    university: str = ""
    target_domains: list[str] = field(default_factory=list)
    max_experience_allowed: int = 2

    def as_prompt_block(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"Degree: {self.degree} ({self.graduating_year} Batch)\n"
            f"University: {self.university}\n"
            f"Target location: {self.target_location}\n"
            f"Open to locations: {', '.join(self.open_to)}\n"
            f"Target domains: {', '.join(self.target_domains) or 'Software Development, Web, Data & AI, Cloud, QA'}\n"
            f"Target titles: {', '.join(self.target_titles)}\n"
            f"Years of Experience: {self.years_experience} (Fresher graduating in {self.graduating_year})\n"
            f"Tech Stack: {', '.join(self.stack)}\n"
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
            "degree": self.degree,
            "graduating_year": self.graduating_year,
            "university": self.university,
            "target_location": self.target_location,
            "open_to": self.open_to,
            "target_domains": self.target_domains,
            "target_titles": self.target_titles,
            "years_experience": self.years_experience,
            "max_experience_allowed": self.max_experience_allowed,
            "stack": self.stack,
            "must_have": self.must_have,
            "nice_to_have": self.nice_to_have,
            "deal_breakers": self.deal_breakers,
            "notice_period": self.notice_period,
            "current_location": self.current_location,
            "ctc_expectation": self.ctc_expectation,
            "work_authorization": self.work_authorization,
            "salary_band": self.salary_band,
            "notes": self.notes,
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
    return Profile(
        name=str(data.get("name") or ""),
        degree=str(data.get("degree") or ""),
        graduating_year=int(data.get("graduating_year") or 2026),
        university=str(data.get("university") or ""),
        target_location=str(data.get("target_location", "Bangalore")),
        open_to=list(data.get("open_to") or []),
        target_domains=list(data.get("target_domains") or []),
        target_titles=list(data.get("target_titles") or []),
        years_experience=int(data.get("years_experience") or 0),
        max_experience_allowed=int(data.get("max_experience_allowed") or 2),
        stack=list(data.get("stack") or []),
        must_have=list(data.get("must_have") or []),
        nice_to_have=list(data.get("nice_to_have") or []),
        deal_breakers=list(data.get("deal_breakers") or []),
        notice_period=str(data.get("notice_period", "Immediate")),
        current_location=str(data.get("current_location", "")),
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
