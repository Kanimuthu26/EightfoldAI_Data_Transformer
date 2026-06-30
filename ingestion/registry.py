from typing import List, Optional, Type
from ingestion.base import SourceAdapter, RawRecord
from ingestion.csv_adapter import CSVAdapter
from ingestion.ats_json_adapter import ATSJsonAdapter
from ingestion.resume_adapter import ResumeAdapter
from ingestion.notes_adapter import NotesAdapter
from ingestion.github_adapter import GitHubAdapter
from ingestion.linkedin_adapter import LinkedInAdapter

ADAPTER_REGISTRY = {
    "csv": CSVAdapter,
    "ats_json": ATSJsonAdapter,
    "resume": ResumeAdapter,
    "notes": NotesAdapter,
    "github": GitHubAdapter,
    "linkedin": LinkedInAdapter
}

def detect_adapter(filepath_or_url: str) -> Optional[SourceAdapter]:
    """
    Scans the registered adapters and returns an instance of the first one
    that detects a match.
    """
    for adapter_class in ADAPTER_REGISTRY.values():
        adapter = adapter_class()
        if adapter.detect(filepath_or_url):
            return adapter
    return None

def detect_and_extract(filepath_or_url: str) -> List[RawRecord]:
    """
    Auto-detects the correct adapter for a given input path or URL,
    and extracts raw records. If no adapter matches, returns an empty list.
    """
    adapter = detect_adapter(filepath_or_url)
    if not adapter:
        return []
    try:
        return adapter.extract(filepath_or_url)
    except Exception:
        # Fallback to empty list as per edge case requirements (do not crash pipeline)
        return []
