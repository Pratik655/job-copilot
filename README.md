# job-copilot

Review-first copilot for Bangalore software-engineer job search. It collects listings, scores them against your profile, drafts an application packet, and **never submits** — you approve, then apply on the original site.

## How it works

1. **Ingest** public Greenhouse / Lever / Ashby boards from `watchlist.yaml`, plus anything you drop in `inbox/` or paste in the UI (LinkedIn, Naukri, Indeed, Wellfound, recruiter mail).
2. **Score + draft** a cover note, resume bullets, screening answers, and a referral message.
3. **You review** at http://127.0.0.1:8765 — edit, approve, skip, or snooze. Approve opens nothing automatically except your own click on the listing URL.

There is no auto-apply. LinkedIn / Naukri / Indeed do not offer a personal apply API; treating them as paste sources avoids account bans and junk applications.

## Setup

```bash
cd ~/Desktop/job-copilot
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `profile/profile.yaml` and `profile/resume.md`. For Cursor-written drafts, put `CURSOR_API_KEY` in `.env` (Dashboard → Integrations). Scoring then uses a local Cursor agent (`composer-2.5` by default) on the job text you already ingested — it does not scrape LinkedIn/Naukri. `OPENAI_API_KEY` is an optional fallback. With neither key, scoring is keyword overlap plus templates.

Cursor agents are slower than a single chat call. Prefer them on pasted roles and a small queue; a full watchlist `run` with Cursor enabled will take a while.

## Daily loop

```bash
cd ~/Desktop/job-copilot
make findjob
```

That ingests the watchlist and `inbox/`, scores new jobs, then opens **http://127.0.0.1:8765**. Use `make serve` if you only want the UI. Cursor scoring of a large new batch will take a while.

Keyboard in the UI: `j` / `k` move, `a` approve, `x` skip, `c` copy cover, `p` paste listing.

Paste a single JD:

```bash
python -m jobcopilot paste inbox/sample-bangalore-swe.md --url 'https://example.com/jobs/…'
```

Add companies to `watchlist.yaml` using the slug from the public careers URL (`boards.greenhouse.io/stripe` → `slug: stripe`, `ats: greenhouse`).
