import pytest
from jobcopilot.resume_parser import parse_resume_text, save_parsed_profile
from jobcopilot.profile import load_profile
from jobcopilot.ai import _heuristic
from jobcopilot.pipeline import rescore_all_jobs
from jobcopilot.db import connect

def test_resume_parsing_and_executive_letter():
    sample_resume = """Hayden Smith
214 Mitre Avenue, Park Hill, 3045 | 04501 123 456 | haydensmith@email.com
Career Objective
I am reliable hard working Year 11 student seeking casual or part-time customer service work in a sports retail environment. Having played soccer for nine years and a keen all-round sports enthusiast, I am looking to contribute knowledge and proven communications skills.
Key Skills
• Customer service ability demonstrated when working efficiently in soccer club canteen.
• Numeracy skills for cash handling tasks proven by achieving good results for mathematics subjects.
Education
Park Hill Secondary College Year 11
Work Experience
December 2016 – March 2017
Park Hill Soccer Club Canteen Customer service (volunteer)
• Served customers and handled cash register.
"""

    parsed = parse_resume_text(sample_resume)
    assert parsed["name"] == "Hayden Smith"
    assert parsed["email"] == "haydensmith@email.com"
    assert "04501 123 456" in parsed["phone"]
    assert "Park Hill" in parsed["current_location"]
    assert "Year 11" in parsed["degree"]
    assert "Park Hill Secondary College" in parsed["university"]
    assert "reliable hard working Year 11 student" in parsed["summary"]
    assert len(parsed["experience_highlights"]) > 0

    # Test cover letter generation with this profile
    job = {
        "id": 999,
        "title": "Customer Support Associate",
        "company": "Decathlon",
        "location": "Melbourne",
        "description": "Seeking enthusiastic customer service and retail assistants."
    }
    result = _heuristic(job, parsed)
    letter = result.get("cover_letter", "")
    assert "Hayden Smith" in letter
    assert "haydensmith@email.com" in letter
    assert "04501 123 456" in letter
    assert "Decathlon" in letter
    assert "reliable hard working Year 11 student" in letter or "customer service" in letter.lower()
