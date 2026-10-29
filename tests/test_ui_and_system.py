import json
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from jobcopilot.web import app


@pytest.fixture
def client():
    return TestClient(app)


def test_home_page_status_and_headers(client):
    """Verify that root page loads cleanly with 200 OK and correct content type."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_home_page_creator_attribution(client):
    """Verify creator attribution to Pratik is present in both header and footer."""
    response = client.get("/")
    html = response.text
    assert "Pratik" in html
    soup = BeautifulSoup(html, "html.parser")
    
    # Check creator badge in top nav
    creator_badge = soup.find(class_="creator-badge")
    assert creator_badge is not None, "Top nav creator badge must be present"
    assert "Pratik" in creator_badge.get_text()

    # Check footer creator stamp
    creator_stamp = soup.find(class_="creator-stamp")
    assert creator_stamp is not None, "Footer creator stamp must be present"
    assert "Pratik Kumar" in creator_stamp.get_text()


def test_essential_dom_elements_exist(client):
    """Verify all critical IDs required by app.js exist in index.html to guarantee zero broken JS references."""
    response = client.get("/")
    soup = BeautifulSoup(response.text, "html.parser")
    
    required_ids = [
        # Navigation
        "navPref", "navJobs", "navPacket", "navJobCount",
        # Views
        "viewPreferences", "viewJobs", "viewPacket",
        # Overlay & Scanner
        "overlay", "overlayText", "scanStepList", "step1", "step2", "step3", "step4",
        # Notifications
        "banner",
        # Actions & Autosync
        "autoSyncWrap", "syncDot", "syncStatusLabel", "toggleAutoSyncBtn",
        "runBtn", "fetchSyncBtn", "moreBtn", "moreMenu", "rescoreBtn", "exportCsvBtn", "exportAllBtn",
        # Step 1: Upload & Profile
        "dropzone", "resumeFileInput", "browseFileBtn",
        "extractedCard", "scanStatusTag", "profName", "profDegree", "profYear", "profUniversity", "profCurrentLoc",
        "skillsChips", "newSkillInput", "addSkillBtn",
        "cityPillsGrid", "customCityInput", "addCustomCityBtn", "selectAllCitiesBtn", "selectTopCitiesBtn", "clearCitiesBtn",
        "domainCardsGrid", "customDomainInput", "addCustomDomainBtn", "selectAllDomainsBtn", "clearDomainsBtn",
        "saveAndContinueBtn",
        # Step 2: Feed & Split Preview
        "statusTabs", "countQueued", "countReady", "countApplied", "countSkipped", "countTotal",
        "search", "domainFilter", "cityFilter", "onlySelectedCitiesToggle",
        "jobsCountLabel", "jobList", "quickPreviewPane", "emptyPreview", "previewContent",
        # Step 3: Application Packet
        "backToJobsBtn", "packetJobHeader", "packetTitle", "packetScoreBadge", "packetCompany", "packetCity", "packetDomain", "packetExp",
        "btnPacketApply", "btnPacketApprove", "btnPacketMarkApplied", "btnPacketSkip",
        "packetFitBreakdown", "fitPillsRow", "matchedSkillsRow",
        "packetTabs", "tabCover", "tabBullets", "tabReferral", "tabQa", "tabJd",
        "coverLetterText", "copyCoverBtn", "resumeBulletsList", "copyBulletsBtn",
        "referralText", "copyReferralBtn", "screeningQaList", "fullJdContent", "originalLinkAnchor",
        "appliedTable", "appliedTableBody", "exportHistoryCsvBtn",
        # Reset & Profile Actions
        "clearProfileBtn", "resetResumeBtn",
        # Modal
        "pasteModal", "pasteCloseBtn", "pasteCancelBtn", "pasteSubmitBtn", "pasteUrl", "pasteText"
    ]

    missing = []
    for elem_id in required_ids:
        if not soup.find(id=elem_id):
            missing.append(elem_id)

    assert not missing, f"Missing critical IDs in index.html: {missing}"


def test_static_assets_serve_correctly(client):
    """Verify styles.css and app.js are served with 200 OK."""
    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]
    assert "creator-badge" in css_res.text
    assert "creator-stamp" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers["content-type"]


def test_api_core_endpoints(client):
    """Verify backend JSON endpoints respond with valid structures."""
    # Stats endpoint
    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "queued" in stats
    assert isinstance(stats["queued"], int)

    # Preferences endpoint
    pref_res = client.get("/api/preferences")
    assert pref_res.status_code == 200
    prefs = pref_res.json()
    assert "profile" in prefs
    assert "all_cities" in prefs
    assert "all_domains" in prefs

    # Filters endpoint
    filters_res = client.get("/api/filters")
    assert filters_res.status_code == 200
    filters_data = filters_res.json()
    assert "cities" in filters_data

    # Jobs list endpoint
    jobs_res = client.get("/api/jobs?status=queued")
    assert jobs_res.status_code == 200
    jobs = jobs_res.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0, "Database should have indexed opportunities"


def test_resume_upload_and_auto_match(client, tmp_path):
    """Test the complete upload -> parse -> save & auto-rescore flow."""
    # Test text scan endpoint
    resume_text = (
        "Candidate Alex Morgan\n"
        "B.Tech in Computer Science and Engineering, 2026\n"
        "National Institute of Technology, Surathkal\n"
        "Skills: Python, FastAPI, React, SQL, Machine Learning, Git, Docker, REST APIs\n"
        "Location: Bangalore, open to Bangalore, Hyderabad, Pune, Remote"
    )
    
    scan_res = client.post("/api/resume/scan-text", json={"text": resume_text})
    assert scan_res.status_code == 200
    parsed_data = scan_res.json()
    assert "parsed" in parsed_data
    parsed = parsed_data["parsed"]
    assert "skills" in parsed
    assert len(parsed["skills"]) > 0

    # Save & rescore
    save_res = client.post(
        "/api/resume/save",
        json={
            "parsed": parsed,
            "raw_text": resume_text,
            "rescore": True,
            "trigger_sync": False,
        },
    )
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["status"] == "saved"
    assert isinstance(save_data["rescored"], dict)
    assert save_data["rescored"]["total_rescored"] > 0

    # Clean up test artifact to leave profile clean for new candidates
    from jobcopilot.paths import get_profile_path, get_resume_path, get_db_path
    import yaml
    import sqlite3
    p_path = get_profile_path()
    r_path = get_resume_path()
    if p_path.exists():
        data = yaml.safe_load(p_path.read_text(encoding="utf-8")) or {}
        data["name"] = ""
        data["degree"] = ""
        data["university"] = ""
        p_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    if r_path.exists():
        r_path.write_text("", encoding="utf-8")
    with sqlite3.connect(get_db_path()) as conn:
        conn.execute("DELETE FROM drafts")
        conn.commit()


def test_no_unwanted_emojis_in_html(client):
    """Verify that index.html contains clean vector SVGs and zero raw emoji characters."""
    import unicodedata
    response = client.get("/")
    html = response.text
    
    # Check that SVG icons are used
    assert "<svg" in html, "Page must use vector SVG icons"
    assert "viewBox" in html, "SVGs must have proper viewBox attributes"
    
    # Check for unwanted emojis (excluding typography quotes, dashes, spark symbol)
    allowed_unicode = {'✦', '—', '…', '’', '“', '”', '•', '–'}
    found_emojis = []
    for idx, line in enumerate(html.splitlines(), 1):
        for ch in line:
            if ord(ch) > 0x2000 and ch not in allowed_unicode:
                cat = unicodedata.category(ch)
                if cat in ('So', 'Sk', 'Sm', 'Cn'):
                    found_emojis.append((idx, ch, unicodedata.name(ch, 'UNKNOWN')))
    
    assert not found_emojis, f"Found unwanted emojis in HTML: {found_emojis}"


