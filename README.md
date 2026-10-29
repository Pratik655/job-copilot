# job-copilot — Advanced B.Tech CSE & Multi-City Edition

Review-first AI copilot for **B.Tech Computer Science & Engineering (2026 Fresher)** job search across **Bangalore, Hyderabad, Pune, Delhi-NCR, Mumbai, Chennai, and Remote India**.

It automatically aggregates listings from public ATS boards (Greenhouse / Lever / Ashby), evaluates eligibility and technical overlap, generates customized application packets (cover letter, domain resume bullets, screening Q&A, and referral notes), and lets you review everything before applying on the official company careers page.

---

## What's New & Advanced

1. **B.Tech CSE Comprehensive Entry-Level Coverage**:
   - **Software Engineering / SDE-1**: SDE-1, Associate Software Engineer, Junior Software Engineer, Member of Technical Staff (MTS-1), Application Engineer.
   - **Full Stack & Web**: Node.js Developer, Python Developer, React Developer, Full Stack Engineer.
   - **Data Science & AI**: Data Analyst, Data Science Intern, Machine Learning Engineer, Junior Data Engineer, BI Analyst.
   - **Quality & Automation (SDET)**: Software Development Engineer in Test (SDET), QA Automation Engineer, Software Test Engineer.
   - **Cloud, DevOps & Systems**: Cloud Engineer, DevOps Associate, Site Reliability Engineer (SRE), Systems Engineer.
   - **Graduate Trainee / Campus**: Graduate Engineer Trainee (GET), Trainee Engineer, Technology Analyst.

2. **Multi-City & Location Intelligence**:
   - Covers all major Indian tech hubs: **Bangalore / Bengaluru**, **Hyderabad**, **Pune**, **Delhi-NCR (Gurgaon/Noida)**, **Mumbai**, **Chennai**, **Kolkata**, **Ahmedabad**, **Chandigarh/Mohali**, **Kochi**, **Trivandrum**, and **Remote India (WFH)**.
   - Smart city normalizer maps micro-locations (e.g. Hitec City, Hinjewadi, Whitefield, OMR, Cyberabad) to canonical tech hubs.

3. **4-Pillar Match Breakdown Engine**:
   - **Degree & Batch Fit (25 pts)**: Checks B.Tech/B.E. CSE/IT eligibility and 2026 fresher allowance.
   - **Role & Seniority Fit (25 pts)**: Prioritizes early-career entry points while filtering out senior/lead roles (>2 yrs exp).
   - **Tech Stack Overlap (30 pts)**: Overlap with Node.js, Express, MongoDB, JavaScript, Python, Pandas, NumPy, REST APIs, Git, and C++.
   - **Location Preference (20 pts)**: High weighting for Bangalore, Remote India, and open Indian tech hubs.

4. **Modern Glassmorphic Web Dashboard**:
   - **Filter Toolbar**: Instant search, City filter dropdown, Domain filter dropdown, Min Score filter, and Status selector.
   - **Fit Analysis Card**: Shows detailed ratings for each pillar, matched skills tags, and clear explanation.
   - **1-Click Copy Packet**: Copy Cover Letter, Domain-Specific Bullets, or Referral Message with one click.
   - **Profile & Search Scope Drawer**: Edit candidate details, open cities, and target domains directly in the browser.
   - **Export CSV / JSON**: Download applications spreadsheet for tracking.
   - **Re-Score All**: Re-evaluate all jobs against the latest scoring criteria in one click.

---

## Quick Start

### Windows (PowerShell / Command Prompt)
```powershell
cd ~\Desktop\job-copilot
.\.venv\Scripts\Activate.ps1
python -m jobcopilot serve
```

### Review UI & CLI Commands
```bash
# Start Web UI (http://127.0.0.1:8765)
python -m jobcopilot serve

# Pull public ATS boards and score new listings
python -m jobcopilot run

# Re-score all jobs against updated profile & filters
python -m jobcopilot rescore

# Export applied or queued jobs to CSV
python -m jobcopilot export --format csv --status queued --out queued_jobs.csv

# Ingest a single pasted job description from LinkedIn / Naukri
python -m jobcopilot paste samples/pasted-jd.md --url "https://company.com/job"
```

---

## Keyboard Shortcuts in Web UI

- `j` / `k` — Move selection down / up through job list
- `a` — Approve application packet
- `x` — Skip job
- `c` — Copy cover letter to clipboard
- `p` — Open "Paste Listing" drawer
- `Escape` — Close any open drawer
