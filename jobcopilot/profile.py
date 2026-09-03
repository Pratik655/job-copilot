from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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

    def as_prompt_block(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"Target location: {self.target_location}\n"
            f"Open to: {', '.join(self.open_to)}\n"
            f"Target titles: {', '.join(self.target_titles)}\n"
            f"Years: {self.years_experience}\n"
            f"Stack: {', '.join(self.stack)}\n"
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


def load_profile(
    profile_path: Path | None = None, resume_path: Path | None = None
) -> Profile:
    profile_path = profile_path or ROOT / "profile" / "profile.yaml"
    resume_path = resume_path or ROOT / "profile" / "resume.md"
    data = yaml.safe_load(profile_path.read_text()) or {}
    resume = resume_path.read_text() if resume_path.exists() else ""
    return Profile(
        name=str(data.get("name", "")),
        target_location=str(data.get("target_location", "Bangalore")),
        open_to=list(data.get("open_to") or []),
        target_titles=list(data.get("target_titles") or []),
        years_experience=int(data.get("years_experience") or 0),
        stack=list(data.get("stack") or []),
        must_have=list(data.get("must_have") or []),
        nice_to_have=list(data.get("nice_to_have") or []),
        deal_breakers=list(data.get("deal_breakers") or []),
        notice_period=str(data.get("notice_period", "")),
        current_location=str(data.get("current_location", "")),
        ctc_expectation=str(data.get("ctc_expectation", "")),
        work_authorization=str(data.get("work_authorization", "")),
        salary_band=str(data.get("salary_band", "")),
        notes=str(data.get("notes", "")),
        resume=resume,
    )
