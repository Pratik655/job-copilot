from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

try:
    import pypdf
except ImportError:
    pypdf = None

from jobcopilot.profile import Profile, load_profile, save_profile
from jobcopilot.settings import ROOT

# Comprehensive skill dictionaries across Tech, Data, Marketing, Sales, Product, Ops, Consulting, Operations
KNOWN_SKILLS: dict[str, list[str]] = {
    "tech": [
        "python", "javascript", "typescript", "c++", "c#", "java", "go", "rust",
        "node.js", "nodejs", "express", "express.js", "react", "react.js", "next.js",
        "vue", "angular", "html", "css", "tailwind", "redux", "fastapi", "django", "flask",
        "sql", "postgresql", "mysql", "mongodb", "redis", "sqlite",
        "git", "github", "docker", "kubernetes", "aws", "gcp", "azure", "linux",
        "rest api", "graphql", "microservices", "ci/cd", "postman", "sdet", "selenium"
    ],
    "data": [
        "pandas", "numpy", "scipy", "scikit-learn", "matplotlib", "seaborn",
        "machine learning", "deep learning", "ai", "nlp", "computer vision",
        "pytorch", "tensorflow", "power bi", "tableau", "excel", "data analysis",
        "data visualization", "sql", "bigquery", "spark", "hadoop", "eda"
    ],
    "marketing": [
        "digital marketing", "seo", "sem", "content marketing", "social media marketing",
        "copywriting", "email marketing", "google analytics", "meta ads", "facebook ads",
        "performance marketing", "brand strategy", "growth hacking", "influencer marketing",
        "campaign management", "public relations"
    ],
    "sales_bd": [
        "sales", "business development", "lead generation", "cold calling", "cold emailing",
        "crm", "salesforce", "hubspot", "client relationship", "b2b sales",
        "customer success", "solution selling", "negotiation", "pitching", "account management"
    ],
    "product_ops": [
        "product management", "agile", "scrum", "jira", "wireframing", "figma",
        "market research", "user stories", "roadmap", "operations management",
        "process optimization", "supply chain", "logistics", "strategy & operations"
    ],
    "consulting_biz": [
        "business analysis", "financial modeling", "market research", "swot analysis",
        "strategic planning", "consulting", "stakeholder management", "problem solving"
    ],
    "operations_service": [
        "customer service", "client service", "cash handling", "canteen", "retail",
        "store management", "inventory", "hospitality", "event management",
        "teamwork", "organization", "problem solving", "communication"
    ],
    "general": [
        "communication", "team collaboration", "critical thinking", "problem solving",
        "adaptability", "project management", "presentation skills"
    ]
}

INDIAN_TECH_CITIES: list[str] = [
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Delhi-NCR",
    "Mumbai",
    "Chennai",
    "Kolkata",
    "Ahmedabad",
    "Remote India",
    "Chandigarh",
    "Mohali",
    "Kochi",
    "Trivandrum",
    "Coimbatore",
    "Jaipur",
    "Indore",
    "Lucknow",
    "Bhubaneswar",
    "Nagpur",
    "Vadodara",
    "Bhopal",
    "Visakhapatnam",
]

AVAILABLE_DOMAINS: list[dict[str, str]] = [
    {"key": "tech", "label": "Software & Tech", "desc": "SDE, Web, Backend, Frontend, Cloud, DevOps"},
    {"key": "data", "label": "Data & Analytics", "desc": "Data Analyst, BI, Data Science, AI/ML"},
    {"key": "product_ops", "label": "Product & Operations", "desc": "APM, Product Analyst, Operations Associate"},
    {"key": "marketing", "label": "Marketing & Growth", "desc": "Digital Marketing, SEO, Social Media, Growth"},
    {"key": "sales_bd", "label": "Sales & Business Dev", "desc": "Solutions Eng, BDA, Inside Sales, Customer Success"},
    {"key": "trainee_campus", "label": "Graduate Trainee / GET", "desc": "Campus Freshers, Trainee Engineer, GET"},
    {"key": "consulting_biz", "label": "Business & Consulting", "desc": "Business Analyst, Strategy, Research"},
    {"key": "hr_talent", "label": "HR & People", "desc": "Recruiting, People Ops, Talent Acquisition"},
]


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """Extract clean text from PDF, Markdown, or plain text file."""
    fn = filename.lower()
    if fn.endswith(".pdf"):
        if not pypdf:
            raise RuntimeError("pypdf is required to parse PDF resumes.")
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages_text: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            pages_text.append(t)
        return "\n".join(pages_text)
    
    # Text or Markdown
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def parse_resume_text(text: str) -> dict[str, Any]:
    """Parse raw resume text into structured candidate information."""
    clean = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l.strip() for l in clean.split("\n") if l.strip()]

    # 1. Email extraction
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean)
    email = email_match.group(0) if email_match else ""

    # 2. Phone extraction (handles international, standard Indian, and spaced formats)
    phone = ""
    phone_match = re.search(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}", clean)
    if phone_match and len(re.sub(r"\D", "", phone_match.group(0))) >= 8:
        phone = phone_match.group(0).strip()

    # 3. Candidate Name extraction (first lines, skipping contact headers)
    name = ""
    for l in lines[:8]:
        if any(h in l.lower() for h in ("resume", "curriculum", "phone", "email", "@", "github", "linkedin", "http", "page ", "curriculum vitae")):
            continue
        cleaned_line = re.sub(r"[^a-zA-Z\s]", "", l).strip()
        words = cleaned_line.split()
        if 1 <= len(words) <= 4:
            name = cleaned_line.title()
            break

    # 4. Location extraction from header lines
    location = ""
    for l in lines[1:8]:
        if "@" in l or (phone and phone in l) or "|" in l:
            parts = [p.strip() for p in l.split("|")]
            for p in parts:
                if "@" not in p and not re.search(r"\d{7,}", p) and not any(k in p.lower() for k in ("http", "github", "linkedin")):
                    if len(p) >= 3 and not p.lower().startswith("phone"):
                        location = p
                        break
            if location:
                break
        elif any(c in l for c in (",", "-")) and len(l) < 50:
            if not any(k in l.lower() for k in ("university", "college", "school", "b.tech", "engineer", "summary", "objective")):
                location = l
                break

    # 5. Section Partitioning (Summary / Objective, Experience, Education, Projects)
    section_headers = [
        "career objective", "objective", "professional summary", "summary", "profile", "about me",
        "availability", "key skills", "skills", "technical skills", "core competencies",
        "education", "academic background", "qualifications",
        "experience", "work experience", "professional experience", "internships", "employment history",
        "projects", "personal projects", "academic projects", "key projects",
        "leadership roles", "interests/hobbies", "referees", "certifications"
    ]

    summary = ""
    experience_highlights: list[str] = []
    projects_summary: list[str] = []

    for idx, l in enumerate(lines):
        clean_hdr = re.sub(r"[^a-z/\s]", "", l.lower()).strip()
        if clean_hdr in ("career objective", "objective", "professional summary", "summary", "profile", "about me"):
            buf = []
            for next_line in lines[idx + 1:]:
                nl_clean = re.sub(r"[^a-z/\s]", "", next_line.lower()).strip()
                if any(nl_clean == sh for sh in section_headers if sh != clean_hdr):
                    break
                if next_line.startswith("(") and next_line.endswith(")"):
                    continue
                buf.append(next_line)
            summary = " ".join(buf).strip()

        elif clean_hdr in ("experience", "work experience", "professional experience", "internships", "employment history"):
            for next_line in lines[idx + 1:]:
                nl_clean = re.sub(r"[^a-z/\s]", "", next_line.lower()).strip()
                if any(nl_clean == sh for sh in section_headers if sh != clean_hdr):
                    break
                if next_line.startswith("(") and next_line.endswith(")"):
                    continue
                cleaned_exp = re.sub(r"^[•\-\*\d\.\s]+", "", next_line).strip()
                if cleaned_exp and len(cleaned_exp) > 10:
                    experience_highlights.append(cleaned_exp)

        elif clean_hdr in ("projects", "personal projects", "academic projects", "key projects"):
            for next_line in lines[idx + 1:]:
                nl_clean = re.sub(r"[^a-z/\s]", "", next_line.lower()).strip()
                if any(nl_clean == sh for sh in section_headers if sh != clean_hdr):
                    break
                if next_line.startswith("(") and next_line.endswith(")"):
                    continue
                cleaned_proj = re.sub(r"^[•\-\*\d\.\s]+", "", next_line).strip()
                if cleaned_proj and len(cleaned_proj) > 10:
                    projects_summary.append(cleaned_proj)

    # 6. Degree detection
    degree = ""
    lower_text = clean.lower()
    if "b.tech" in lower_text or "bachelor of technology" in lower_text:
        if "computer science" in lower_text or "cse" in lower_text:
            degree = "B.Tech in Computer Science and Engineering (CSE)"
        elif "information technology" in lower_text or "it" in lower_text:
            degree = "B.Tech in Information Technology (IT)"
        elif "electronics" in lower_text or "ece" in lower_text:
            degree = "B.Tech in Electronics and Communication (ECE)"
        else:
            degree = "B.Tech"
    elif "b.e." in lower_text or "bachelor of engineering" in lower_text:
        degree = "B.E. in Computer Science & Engineering"
    elif "bba" in lower_text or "bachelor of business" in lower_text:
        degree = "BBA (Bachelor of Business Administration)"
    elif "bca" in lower_text or "bachelor of computer applications" in lower_text:
        degree = "BCA (Bachelor of Computer Applications)"
    elif "mba" in lower_text or "master of business" in lower_text:
        degree = "MBA (Master of Business Administration)"
    elif "mca" in lower_text:
        degree = "MCA (Master of Computer Applications)"
    elif "b.com" in lower_text:
        degree = "B.Com"
    elif "b.sc" in lower_text:
        degree = "B.Sc"
    elif "year 11" in lower_text or "year 12" in lower_text:
        yr = "Year 11" if "year 11" in lower_text else "Year 12"
        degree = f"{yr} Student"
    elif "diploma" in lower_text:
        degree = "Diploma Candidate"

    # 7. Graduating Year
    grad_year = 2026
    year_matches = re.findall(r"\b(202[3-8])\b", clean)
    if year_matches:
        valid_years = [int(y) for y in year_matches if 2024 <= int(y) <= 2028]
        if valid_years:
            grad_year = max(valid_years)

    # 8. University / College / School
    university = ""
    for line in lines:
        if any(w in line.lower() for w in ("university", "institute of technology", "college", "campus", "polytechnic", "school")):
            cleaned_uni = re.sub(r"\b20\d\d\s*[-–—]\s*20\d\d\b", "", line).strip()
            cleaned_uni = re.sub(r"\s+", " ", cleaned_uni).strip()
            if cleaned_uni and not any(k in cleaned_uni.lower() for k in ("experience", "skills", "summary")):
                university = cleaned_uni
                if len(university) > 60:
                    university = university[:60].strip()
                break

    # 9. Skills Matching
    found_skills: set[str] = set()
    domain_counts: dict[str, int] = {k: 0 for k in KNOWN_SKILLS}

    for dom, skill_list in KNOWN_SKILLS.items():
        for sk in skill_list:
            pattern = r"\b" + re.escape(sk) + r"\b"
            if re.search(pattern, lower_text):
                found_skills.add(sk.title() if len(sk) > 3 else sk.upper())
                domain_counts[dom] += 1

    display_map = {
        "Node.Js": "Node.js", "Express.Js": "Express.js", "React.Js": "React",
        "Next.Js": "Next.js", "Javascript": "JavaScript", "Typescript": "TypeScript",
        "Mongodb": "MongoDB", "Postgresql": "PostgreSQL", "Sql": "SQL", "Git": "Git",
        "Docker": "Docker", "Aws": "AWS", "Rest Api": "REST APIs", "Power Bi": "Power BI",
        "Html": "HTML", "Css": "CSS", "Seo": "SEO", "Sem": "SEM", "Crm": "CRM"
    }
    curated_skills = [display_map.get(s, s) for s in sorted(found_skills)]

    # 10. Recommended Target Domains
    recommended_domains: list[str] = []
    if domain_counts["tech"] >= 3:
        recommended_domains.append("tech")
    if domain_counts["data"] >= 2:
        recommended_domains.append("data")
    if domain_counts["marketing"] >= 2 or "marketing" in lower_text:
        recommended_domains.append("marketing")
    if domain_counts["sales_bd"] >= 2 or "sales" in lower_text or "bd" in lower_text:
        recommended_domains.append("sales_bd")
    if domain_counts["product_ops"] >= 2 or "product" in lower_text or "operations" in lower_text:
        recommended_domains.append("product_ops")
    if "trainee" in lower_text or "fresh" in lower_text or grad_year >= 2025:
        recommended_domains.append("trainee_campus")

    if not recommended_domains:
        recommended_domains = ["tech", "data", "product_ops", "trainee_campus"]

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "current_location": location,
        "degree": degree,
        "graduating_year": grad_year,
        "university": university,
        "skills": curated_skills,
        "summary": summary,
        "experience_highlights": experience_highlights[:5],
        "projects_summary": projects_summary[:5],
        "recommended_domains": recommended_domains,
        "skills_count": len(curated_skills),
        "raw_text_length": len(clean),
    }


def save_parsed_profile(parsed: dict[str, Any], raw_text: str | None = None) -> dict[str, Any]:
    """Save parsed resume information into profile.yaml and resume.md, completely replacing previous resume data."""
    from jobcopilot.paths import get_profile_path, get_resume_path

    profile_path = get_profile_path()
    resume_path = get_resume_path()

    new_profile = {
        "name": parsed.get("name") or "",
        "email": parsed.get("email") or "",
        "phone": parsed.get("phone") or "",
        "degree": parsed.get("degree") or "",
        "graduating_year": int(parsed.get("graduating_year") or 2026),
        "university": parsed.get("university") or "",
        "target_location": parsed.get("target_location") or "",
        "current_location": parsed.get("current_location") or "",
        "open_to": [
            "Bangalore", "Hyderabad", "Pune", "Delhi-NCR", "Mumbai",
            "Chennai", "Kolkata", "Ahmedabad", "Remote India"
        ],
        "target_domains": parsed.get("recommended_domains") or ["tech", "data", "trainee_campus"],
        "target_titles": [
            "Software Engineer", "SDE-1", "Full Stack Developer", "Python Developer", "Data Analyst"
        ],
        "years_experience": 0,
        "max_experience_allowed": 2,
        "stack": parsed.get("skills") or [],
        "summary": parsed.get("summary") or "",
        "experience_highlights": parsed.get("experience_highlights") or [],
        "projects_summary": parsed.get("projects_summary") or [],
        "must_have": [],
        "nice_to_have": [],
        "deal_breakers": [],
        "notice_period": "Immediate",
        "ctc_expectation": "Open to discuss for entry-level / fresher roles",
        "work_authorization": "Authorized to work in India",
        "salary_band": "",
        "notes": "",
        "resume": raw_text or "",
    }

    # Write profile.yaml
    save_profile(new_profile, profile_path=profile_path)

    # Overwrite resume.md with the new raw text
    try:
        resume_path.parent.mkdir(parents=True, exist_ok=True)
        resume_path.write_text(raw_text or "", encoding="utf-8")
    except OSError:
        tmp_resume = Path("/tmp") / "resume.md"
        tmp_resume.write_text(raw_text or "", encoding="utf-8")

    return new_profile
