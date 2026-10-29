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

# Comprehensive skill dictionaries across Tech, Data, Marketing, Sales, Product, Ops, Consulting
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

    # 2. Phone extraction
    phone_match = re.search(r"(?:\+?91[\s-]?)?[6-9]\d{9}", clean)
    phone = phone_match.group(0) if phone_match else ""

    # 3. Candidate Name extraction (first lines, skipping headers)
    name = ""
    for l in lines[:6]:
        if any(h in l.lower() for h in ("resume", "curriculum", "phone", "email", "@", "github", "linkedin", "http")):
            continue
        cleaned_line = re.sub(r"[^a-zA-Z\s]", "", l).strip()
        words = cleaned_line.split()
        if 1 <= len(words) <= 4:
            name = cleaned_line.title()
            break

    # 4. Degree detection
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

    # 5. Graduating Year
    grad_year = 2026
    year_matches = re.findall(r"\b(202[3-8])\b", clean)
    if year_matches:
        # Pick the most forward-looking year within reasonable graduating range
        valid_years = [int(y) for y in year_matches if 2024 <= int(y) <= 2028]
        if valid_years:
            grad_year = max(valid_years)

    # 6. University / College
    university = ""
    for line in lines:
        if any(w in line.lower() for w in ("university", "institute of technology", "college", "campus", "polytechnic")):
            cleaned_uni = re.sub(r"\b20\d\d\s*[-–—]\s*20\d\d\b", "", line).strip()
            cleaned_uni = re.sub(r"\s+", " ", cleaned_uni).strip()
            if cleaned_uni:
                university = cleaned_uni
                if len(university) > 60:
                    university = university[:60].strip()
                break

    # 7. Skills Matching
    found_skills: set[str] = set()
    domain_counts: dict[str, int] = {k: 0 for k in KNOWN_SKILLS}

    for dom, skill_list in KNOWN_SKILLS.items():
        for sk in skill_list:
            pattern = r"\b" + re.escape(sk) + r"\b"
            if re.search(pattern, lower_text):
                # Standardize display casing
                found_skills.add(sk.title() if len(sk) > 3 else sk.upper())
                domain_counts[dom] += 1

    # Format specific tech names nicely
    display_map = {
        "Node.Js": "Node.js", "Express.Js": "Express.js", "React.Js": "React",
        "Next.Js": "Next.js", "Javascript": "JavaScript", "Typescript": "TypeScript",
        "Mongodb": "MongoDB", "Postgresql": "PostgreSQL", "Sql": "SQL", "Git": "Git",
        "Docker": "Docker", "Aws": "AWS", "Rest Api": "REST APIs", "Power Bi": "Power BI",
        "Html": "HTML", "Css": "CSS", "Seo": "SEO", "Sem": "SEM", "Crm": "CRM"
    }
    curated_skills = [display_map.get(s, s) for s in sorted(found_skills)]

    # 8. Recommended Target Domains based on match density
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
        "degree": degree,
        "graduating_year": grad_year,
        "university": university,
        "skills": curated_skills,
        "recommended_domains": recommended_domains,
        "skills_count": len(curated_skills),
        "raw_text_length": len(clean),
    }


def save_parsed_profile(parsed: dict[str, Any], raw_text: str | None = None) -> dict[str, Any]:
    """Save parsed resume information into profile.yaml and resume.md."""
    from jobcopilot.paths import get_profile_path, get_resume_path

    profile_path = get_profile_path()
    resume_path = get_resume_path()

    current = load_profile(profile_path, resume_path).to_dict()

    if parsed.get("name"):
        current["name"] = parsed["name"]
    if parsed.get("degree"):
        current["degree"] = parsed["degree"]
    if parsed.get("graduating_year"):
        current["graduating_year"] = int(parsed["graduating_year"])
    if parsed.get("university"):
        current["university"] = parsed["university"]
    if parsed.get("skills"):
        current["stack"] = parsed["skills"]
    if parsed.get("recommended_domains"):
        current["target_domains"] = parsed["recommended_domains"]

    # Write profile.yaml
    save_profile(current, profile_path=profile_path)

    # Write resume.md if raw text is provided
    if raw_text:
        try:
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            resume_path.write_text(raw_text, encoding="utf-8")
        except OSError:
            tmp_resume = Path("/tmp") / "resume.md"
            tmp_resume.write_text(raw_text, encoding="utf-8")

    return current
