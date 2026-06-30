import os
import tempfile
import pytest
from ingestion.base import RawRecord
from ingestion.csv_adapter import CSVAdapter
from ingestion.ats_json_adapter import ATSJsonAdapter
from engine.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill
from engine.match import MatchStrategy
from engine.merge import ProfileMerger
from engine.confidence import compute_overall_confidence
from engine.pipeline import UnificationPipeline
from projection.project import project_profile, resolve_path
from projection.validate import validate_projected_output

# ----------------- 1. Normalization Tests -----------------

def test_phone_normalization():
    assert normalize_phone("+1 (555) 019-2834") == "+15550192834"
    assert normalize_phone("5551234567") == "+15551234567"
    assert normalize_phone("+44 7911 123456") == "+447911123456"
    assert normalize_phone(None) is None
    assert normalize_phone("") is None

def test_date_normalization():
    assert normalize_date("June 2020") == "2020-06"
    assert normalize_date("06/2020") == "2020-06"
    assert normalize_date("2020") == "2020-01"
    assert normalize_date("Present") == "Present"
    assert normalize_date("unknown") is None

def test_country_normalization():
    assert normalize_country("United States") == "US"
    assert normalize_country("USA") == "US"
    assert normalize_country("India") == "IN"
    assert normalize_country("Canada") == "CA"
    assert normalize_country("ZZ") == "ZZ" # unknown but retained
    assert normalize_country(None) is None

def test_skill_normalization():
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("javascript") == "JavaScript"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("c plus plus") == "C++"
    assert normalize_skill("ReactJS") == "React"
    assert normalize_skill("custom_skill") == "custom_skill" # unmodified

# ----------------- 2. Matching Tests -----------------

def test_matching_strategy():
    match = MatchStrategy()
    
    # Register candidate 1
    cand_id_1, is_new_1 = match.resolve_candidate_id(["alice@example.com"], ["+15551234567"])
    assert is_new_1 is True
    
    # Match candidate 1 by email
    cand_id_2, is_new_2 = match.resolve_candidate_id(["ALICE@example.com"], [])
    assert cand_id_2 == cand_id_1
    assert is_new_2 is False

    # Match candidate 1 by phone (email is absent on incoming side)
    cand_id_3, is_new_3 = match.resolve_candidate_id([], ["+15551234567"])
    assert cand_id_3 == cand_id_1
    assert is_new_3 is False

    # Conflicting emails with same phone must NOT merge (as both sides have emails, but different)
    cand_id_4, is_new_4 = match.resolve_candidate_id(["bob@example.com"], ["+15551234567"])
    assert cand_id_4 != cand_id_1
    assert is_new_4 is True

    # Standalone profile (no email/phone)
    cand_id_5, is_new_5 = match.resolve_candidate_id([], [])
    assert cand_id_5 != cand_id_1
    assert is_new_5 is True

# ----------------- 3. Merge & Priority Tests -----------------

def test_priority_merging():
    # ATS JSON > Recruiter CSV > Resume > Recruiter Notes
    merger = ProfileMerger(priority_list=["ATS JSON", "Recruiter CSV", "Resume", "Recruiter Notes"])
    
    records = [
        # Name from Recruiter notes (priority 4)
        RawRecord(field="full_name", value="Alice Cooper", source="Recruiter Notes", method="regex_extraction", record_id="r1"),
        # Name from Recruiter CSV (priority 2)
        RawRecord(field="full_name", value="Alice A. Cooper", source="Recruiter CSV", method="direct_read", record_id="r2"),
        # Headline from Resume (priority 3)
        RawRecord(field="headline", value="Software Developer", source="Resume", method="inference", record_id="r3"),
        # Email from Recruiter Notes (priority 4)
        RawRecord(field="emails", value="alice@notes.com", source="Recruiter Notes", method="regex_extraction", record_id="r1"),
        # Email from ATS JSON (priority 1)
        RawRecord(field="emails", value="alice@ats.com", source="ATS JSON", method="direct_read", record_id="r4")
    ]
    
    profile = merger.merge("cand_123", records)
    
    # Verification: Name should resolve to CSV (higher trust than Notes)
    assert profile.full_name == "Alice A. Cooper"
    
    # Headline should resolve to Resume (since ATS / CSV didn't supply it)
    assert profile.headline == "Software Developer"
    
    # Emails list contains both but sorted or unique.
    # The list is unified across all sources.
    assert "alice@ats.com" in profile.emails
    assert "alice@notes.com" in profile.emails

    # Check that provenance exists for all fields
    provenances = {p.field: p.source for p in profile.provenance}
    assert provenances["full_name"] == "Recruiter CSV"
    assert provenances["headline"] == "Resume"

# ----------------- 4. Edge Cases: Corrupted Files -----------------

def test_corrupted_csv_handling():
    adapter = CSVAdapter()
    
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as temp_f:
        temp_f.write("corrupted,header,line,without,newlines\nand,unmatched,quotes,\"value")
        temp_path = temp_f.name

    try:
        # Should return empty records list instead of crashing
        records = adapter.extract(temp_path)
        assert isinstance(records, list)
        assert len(records) == 0
    finally:
        os.remove(temp_path)

def test_corrupted_json_handling():
    adapter = ATSJsonAdapter()
    
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as temp_f:
        temp_f.write("{ invalid json structure: [1, 2, }")
        temp_path = temp_f.name

    try:
        # Should return empty records list instead of crashing
        records = adapter.extract(temp_path)
        assert isinstance(records, list)
        assert len(records) == 0
    finally:
        os.remove(temp_path)

# ----------------- 5. Projection & Validation Tests -----------------

def test_projection_and_validation():
    # Setup a CanonicalProfile
    from engine.canonical import CanonicalProfile, CanonicalSkill
    profile = CanonicalProfile(
        candidate_id="cand_test",
        full_name="Bob Smith",
        emails=["bob@example.com", "bob.work@example.com"],
        phones=["+15551234567"]
    )
    profile.skills = [
        CanonicalSkill(name="Python", confidence=0.9, sources=["ATS JSON"]),
        CanonicalSkill(name="JavaScript", confidence=0.7, sources=["Resume"])
    ]
    profile.location = {"city": "San Francisco", "region": "CA", "country": "US"}
    
    # Configuration
    config = {
        "fields": [
            { "path": "id", "from": "candidate_id", "type": "string" },
            { "path": "name", "from": "full_name", "type": "string", "required": True },
            { "path": "email", "from": "emails[0]", "type": "string" },
            { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "upper" },
            { "path": "country", "from": "location.country", "type": "string" },
            { "path": "missing_field", "type": "string" }
        ],
        "include_confidence": True,
        "on_missing": "null"
    }

    # Run projection
    projected = project_profile(profile, config)
    
    assert projected["id"] == "cand_test"
    assert projected["name"] == "Bob Smith"
    assert projected["email"] == "bob@example.com"
    assert projected["skills"] == ["PYTHON", "JAVASCRIPT"]
    assert projected["country"] == "US"
    assert projected["missing_field"] is None
    assert "overall_confidence" in projected

    # Type validation override
    # If the user specifies expected type is number, but we output string, validation should set it to None
    mismatched_config = [
        { "path": "id", "type": "number" }, # expected number, but is string
        { "path": "skills", "type": "string[]" }
    ]
    
    validated = validate_projected_output(projected, mismatched_config)
    assert validated["id"] is None  # corrected/nulled out
    assert validated["skills"] == ["PYTHON", "JAVASCRIPT"]
