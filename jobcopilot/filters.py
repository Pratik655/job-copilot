from __future__ import annotations

import re
from typing import Any
# Backward-compatibility alias
SOFTWARE_TITLE_HINTS = ("engineer", "developer", "analyst", "trainee", "associate", "intern", "specialist")

# ==============================================================================
# SENIORITY EXCLUSIONS (Strictly filter out senior/staff/director levels)
# ==============================================================================
SENIORITY_EXCLUDE_PATTERNS = (
    r"\bsenior\b",
    r"\bsr\.?\s+",
    r"\bsr\b",
    r"\bsr-",
    r"\blead\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\barchitect\b",
    r"\bdirector\b",
    r"\bhead\s+of\b",
    r"\bhead[, -]",
    r"\bvp\b",
    r"\bvice\s+president\b",
    r"\bpartner\b",
    r"\bdistinguished\b",
    r"\bfellow\b",
    r"\bsde\s*[-_]?\s*(?:2|ii|3|iii|4|iv|5|v)\b",
    r"\bsoftware\s+engineer\s+(?:2|ii|3|iii|4|iv)\b",
    r"\bengineer\s+(?:2|ii|3|iii|4|iv)\b",
    r"\bdeveloper\s+(?:2|ii|3|iii|4|iv)\b",
    r"\b(?:ii|iii|iv|v|vi)\b",
    r"[-_ ]\s*[2-6]\b",
    r"\bexperienced\b",
)

# Irrelevant non-corporate / manual trades to exclude
MANUAL_EXCLUDE_HINTS = (
    "driver",
    "security guard",
    "housekeeping",
    "delivery boy",
    "cook",
    "waiter",
    "electrician",
    "plumber",
)

# ==============================================================================
# EXPANDED CITY DIRECTORY & NORMALIZATION
# ==============================================================================
CITY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Bangalore": (
        "bangalore", "bengaluru", "blr", "whitefield", "electronic city",
        "koramangala", "bellandur", "marathahalli", "indiranagar", "hsr layout",
        "sarjapur", "manyata", "bagmane"
    ),
    "Hyderabad": (
        "hyderabad", "secunderabad", "hyd", "cyberabad", "gachibowli",
        "hitec city", "hiteccity", "madhapur", "kondapur", "kukatpally", "nanakramguda"
    ),
    "Pune": (
        "pune", "hinjewadi", "hinjawadi", "magarpatta", "kharadi",
        "viman nagar", "vimannagar", "pimpri", "chinchwad", "baner", "wakad"
    ),
    "Delhi-NCR": (
        "gurgaon", "gurugram", "noida", "greater noida", "delhi", "new delhi",
        "faridabad", "ghaziabad", "ncr", "national capital region"
    ),
    "Mumbai": (
        "mumbai", "navi mumbai", "thane", "andheri", "bandra", "powai",
        "goregaon", "malad", "lower parel", "bkc", "airoli"
    ),
    "Chennai": (
        "chennai", "madras", "omr", "tidel", "guindy", "sholinganallur",
        "siruseri", "tharamani", "perungudi"
    ),
    "Kolkata": (
        "kolkata", "calcutta", "salt lake", "saltlake", "new town", "sector v"
    ),
    "Ahmedabad": (
        "ahmedabad", "gandhinagar", "gift city"
    ),
    "Chandigarh": (
        "chandigarh", "mohali", "panchkula"
    ),
    "Kochi": (
        "kochi", "cochin", "infopark", "kakkanad", "ernakulam"
    ),
    "Trivandrum": (
        "trivandrum", "thiruvananthapuram", "technopark"
    ),
    "Indore": (
        "indore", "crystal it park"
    ),
    "Jaipur": (
        "jaipur", "sitapura", "malviya nagar"
    ),
    "Coimbatore": (
        "coimbatore", "tidel park coimbatore"
    ),
    "Bhubaneswar": (
        "bhubaneswar", "infocity"
    ),
    "Remote India": (
        "remote - india", "remote in india", "remote (india)", "india remote",
        "remote, india", "remote india", "pan-india", "pan india", "anywhere in india",
        "work from home - india", "wfh india", "remote (anywhere)"
    ),
}

BANGALORE_HINTS = CITY_PATTERNS["Bangalore"]

INDIA_HINTS = (
    "india",
    "indian",
    "karnataka",
    "telangana",
    "maharashtra",
    "tamil nadu",
    "haryana",
    "uttar pradesh",
    "west bengal",
    "gujarat",
    "kerala",
    "punjab",
    "rajasthan",
    "madhya pradesh",
    "odisha",
    "jharkhand",
)

REMOTE_HINTS = ("remote", "hybrid", "anywhere", "work from home", "wfh")

FOREIGN_LOCATIONS = (
    "united states", "usa", "u.s.", "san francisco", "new york", "seattle", "austin",
    "california", "texas", "washington", "boston", "chicago", "los angeles",
    "united kingdom", "london", "uk", "germany", "berlin", "munich",
    "france", "paris", "canada", "toronto", "vancouver", "australia", "sydney", "melbourne",
    "ireland", "dublin", "netherlands", "amsterdam", "italy", "milan", "rome",
    "singapore", "japan", "tokyo", "nordics", "sweden", "norway", "poland", "brazil",
    "israel", "dubai", "uae"
)


def normalize_city(location: str | None, description: str | None = None) -> str:
    """Standardize raw location into a canonical Indian tech city name or Remote India."""
    loc = (location or "").lower()
    desc = (description or "")[:1500].lower()
    combined = f"{loc} {desc}"

    for pattern in CITY_PATTERNS["Remote India"]:
        if pattern in loc:
            return "Remote India"

    for city_name, patterns in CITY_PATTERNS.items():
        if city_name == "Remote India":
            continue
        if any(p in loc for p in patterns):
            if "remote" in loc or "hybrid" in loc:
                return f"{city_name} (Hybrid/Remote)"
            return city_name

    if any(r in loc for r in REMOTE_HINTS):
        for city_name, patterns in CITY_PATTERNS.items():
            if city_name == "Remote India":
                continue
            if any(p in desc for p in patterns):
                return f"{city_name} (Remote)"
        if any(ih in combined for ih in INDIA_HINTS) or "india" in loc:
            return "Remote India"
        return "Remote"

    if any(ih in loc for ih in INDIA_HINTS):
        for city_name, patterns in CITY_PATTERNS.items():
            if any(p in desc for p in patterns):
                return city_name
        return "India"

    return location.strip() if location else "Flexible / India"


def is_location_relevant(
    location: str | None,
    description: str | None = None,
    allowed_cities: list[str] | None = None,
) -> bool:
    """Check if the job is in any supported Indian city or Remote India."""
    loc = (location or "").lower().strip()
    desc = (description or "")[:2500].lower()
    combined = f"{loc} {desc}"

    if any(f in loc for f in FOREIGN_LOCATIONS):
        if not any(h in loc for h in INDIA_HINTS) and not any(
            p in loc for p_list in CITY_PATTERNS.values() for p in p_list
        ):
            return False

    for patterns in CITY_PATTERNS.values():
        if any(p in loc for p in patterns):
            return True

    if any(h in loc for h in INDIA_HINTS):
        return True

    if any(h in loc for h in REMOTE_HINTS):
        if any(h in combined for h in INDIA_HINTS):
            return True
        if any(p in combined for p_list in CITY_PATTERNS.values() for p in p_list):
            return True
        if any(
            h in combined
            for h in (
                "india", "indian", "bangalore", "bengaluru", "hyderabad",
                "pune", "delhi", "gurgaon", "noida", "chennai", "mumbai"
            )
        ):
            return True

    return False


def is_bangalore_relevant(location: str | None, description: str | None = None) -> bool:
    return is_location_relevant(location, description)


# ==============================================================================
# BROAD DOMAIN & FIELD CLASSIFICATION (Tech, Marketing, Sales, Product, Ops, BBA)
# ==============================================================================
DOMAIN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "marketing": {
        "label": "Marketing & Growth",
        "hints": (
            "marketing", "growth", "digital marketing", "seo", "sem", "content marketing",
            "social media", "brand", "campaign", "copywriter", "community manager",
            "public relations", "performance marketing", "influencer", "product marketing"
        ),
    },
    "sales_bd": {
        "label": "Sales & Business Dev",
        "hints": (
            "sales", "business development", "bda", "bde", "inside sales", "account executive",
            "account manager", "client servicing", "client relationship", "customer success",
            "customer experience", "partnerships", "solution sales"
        ),
    },
    "product_ops": {
        "label": "Product & Operations",
        "hints": (
            "product manager", "associate product manager", "apm", "product analyst",
            "operations", "program manager", "project coordinator", "operations associate",
            "logistics", "supply chain", "strategy & ops"
        ),
    },
    "data": {
        "label": "Data & Analytics",
        "hints": (
            "data analyst", "data science", "data scientist", "machine learning", "ml",
            "ai", "bi analyst", "business intelligence", "analytics", "analytics associate",
            "market research", "research analyst", "data engineer"
        ),
    },
    "consulting_biz": {
        "label": "Business & Consulting",
        "hints": (
            "business analyst", "consultant", "associate consultant", "management trainee",
            "strategy", "corporate strategy", "advisory", "financial analyst", "equity research"
        ),
    },
    "hr_talent": {
        "label": "HR & Talent Acquisition",
        "hints": (
            "human resources", "hr", "recruiter", "recruiting", "talent acquisition",
            "people operations", "people & culture"
        ),
    },
    "trainee_campus": {
        "label": "Graduate Trainee / GET",
        "hints": (
            "graduate engineer trainee", "get", "trainee engineer", "graduate trainee",
            "management trainee", "campus", "fresher", "intern", "internship", "early career"
        ),
    },
    "tech": {
        "label": "Software & Engineering",
        "hints": (
            "software engineer", "software developer", "sde", "developer", "engineer",
            "full stack", "fullstack", "backend", "frontend", "web developer", "node",
            "python", "javascript", "react", "cloud", "devops", "sdet", "qa",
            "systems engineer", "programmer analyst", "application engineer"
        ),
    },
}


def detect_domain(title: str | None, description: str | None = None) -> tuple[str, str]:
    """Detect domain across Tech, Marketing, Sales, Product, Operations, and Business."""
    t = (title or "").lower()
    d = (description or "")[:2000].lower()
    combined = f"{t} {d}"

    for key, info in DOMAIN_DEFINITIONS.items():
        if any(h in t for h in info["hints"]):
            return key, info["label"]

    for key, info in DOMAIN_DEFINITIONS.items():
        if any(h in combined for h in info["hints"]):
            return key, info["label"]

    return "general", "Graduate & Early Career"


def detect_experience_level(title: str | None, description: str | None = None) -> str:
    t = (title or "").lower()
    d = (description or "")[:2000].lower()

    if any(i in t for i in ("intern", "internship", "trainee")):
        return "Intern / Trainee"
    if any(
        e in t
        for e in (
            "graduate", "associate", "junior", "fresher", "get", "entry level",
            "campus", "new grad", "sde-1", "sde 1", "assistant", "executive"
        )
    ):
        return "Fresher / Entry-Level"
    if "0-1" in d or "0-2" in d or "fresher" in d or "2026" in d or "2025" in d:
        return "Fresher / Entry-Level"
    return "Early Career"


# ==============================================================================
# OPEN ELIGIBILITY & SENIORITY FILTERING
# ==============================================================================
def is_senior_or_experienced(title: str | None, description: str | None = None) -> bool:
    """Check if title strictly requires senior/lead level unsuitable for freshers."""
    t = (title or "").lower()
    for pattern in SENIORITY_EXCLUDE_PATTERNS:
        if re.search(pattern, t):
            return True

    # Exclude senior people/engineering managers (while keeping Associate/Product Manager, APM, Trainee)
    if re.search(r"\bmanager\b", t):
        if not any(k in t for k in ("product", "associate", "trainee", "apm", "assistant")):
            return True

    if description:
        d = description[:3500].lower()
        if any(f in d for f in ("0-1 year", "0-2 year", "fresher", "freshers", "intern", "campus", "2026", "2025")):
            return False
        exp_matches = re.findall(
            r"(?:at least|minimum|\b)(\d+)\+?\s*(?:to\s*\d+\+?\s*)?(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp|hands-on)",
            d,
        )
        for em in exp_matches:
            try:
                if int(em) >= 3:
                    return True
            except (ValueError, TypeError):
                pass

    return False


def is_eligible_role_title(title: str | None) -> bool:
    """Check if the job title is an open early-career/graduate opportunity."""
    t = (title or "").lower().strip()
    if not t:
        return False

    if any(m in t for m in MANUAL_EXCLUDE_HINTS):
        return False

    if is_senior_or_experienced(t):
        return False

    return True


# Backward-compatible alias
def is_software_title(title: str | None) -> bool:
    return is_eligible_role_title(title)


def check_btech_cse_eligibility(
    title: str | None, description: str | None = None
) -> dict[str, Any]:
    t = (title or "").lower()
    d = (description or "")[:3500].lower()
    combined = f"{t} {d}"

    degree_patterns = (
        r"\bb\.?tech\b", r"\bbtech\b", r"\bb\.?e\.?\b", r"\bbe\b",
        r"\bbba\b", r"\bmba\b", r"\bbca\b", r"\bmca\b",
        r"\bbachelor", r"\bdegree\b", r"\bgraduate\b",
        r"\bcomputer\s+science\b", r"\bengineering\b",
    )
    matched = [pat for pat in degree_patterns if re.search(pat, combined)]

    is_fresher_friendly = any(
        k in combined
        for k in (
            "fresher", "freshers", "2026", "2025", "campus", "new grad",
            "entry level", "early career", "intern", "trainee", "0-1", "0-2",
            "college", "no experience required"
        )
    )

    return {
        "eligible": not is_senior_or_experienced(t, d),
        "is_fresher_friendly": is_fresher_friendly,
        "degree_matched": matched[:4],
        "too_experienced": is_senior_or_experienced(t, d),
    }


def keep_job(title: str | None, location: str | None, description: str | None) -> bool:
    """Keep and score any early-career/graduate job located in India or Remote."""
    return is_eligible_role_title(title) and is_location_relevant(location, description)
