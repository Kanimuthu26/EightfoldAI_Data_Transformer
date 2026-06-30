from typing import List, Dict, Tuple
from ingestion.base import RawRecord
from ingestion.registry import detect_and_extract
from engine.canonical import CanonicalProfile
from engine.normalize import normalize_phone, normalize_skill
from engine.match import MatchStrategy
from engine.merge import ProfileMerger
from engine.confidence import compute_overall_confidence

class UnificationPipeline:
    def __init__(self, priority_list: List[str] = None):
        self.match_strategy = MatchStrategy()
        self.priority_list = priority_list or ["ATS JSON", "Recruiter CSV", "Resume", "Recruiter Notes"]

    def run(self, filepaths_or_urls: List[str]) -> List[CanonicalProfile]:
        """
        Orchestrates the entire unification pipeline:
        Ingest -> Normalize -> Match -> Merge -> Confidence -> Return
        """
        # 1. Ingestion
        all_raw_records: List[RawRecord] = []
        for path_or_url in filepaths_or_urls:
            raw_recs = detect_and_extract(path_or_url)
            all_raw_records.extend(raw_recs)

        if not all_raw_records:
            return []

        # 2. Normalization (Basic preprocessing on flat records)
        normalized_records: List[RawRecord] = []
        for r in all_raw_records:
            if r.value is None:
                continue
            
            # Simple field normalization before matching
            val = r.value
            if r.field == "emails":
                val = str(r.value).strip().lower()
            elif r.field == "phones":
                val = normalize_phone(r.value)
            elif r.field == "skills":
                val = normalize_skill(r.value)
                
            normalized_records.append(RawRecord(
                field=r.field,
                value=val,
                source=r.source,
                method=r.method,
                record_id=r.record_id
            ))

        # 3. Matching / Identity Resolution
        # Group records by record_id (representing a single profile from a source)
        records_by_source_id: Dict[str, List[RawRecord]] = {}
        for r in normalized_records:
            records_by_source_id.setdefault(r.record_id, []).append(r)

        # Map each source record_id to a canonical candidate_id
        source_id_to_cand_id: Dict[str, str] = {}
        
        # Reset match index for this run
        self.match_strategy.reset()

        for source_id, recs in records_by_source_id.items():
            # Gather emails and phones for this source profile to match it
            emails = [r.value for r in recs if r.field == "emails" and r.value]
            phones = [r.value for r in recs if r.field == "phones" and r.value]
            
            cand_id, _ = self.match_strategy.resolve_candidate_id(emails, phones)
            source_id_to_cand_id[source_id] = cand_id

        # Group raw records by their resolved candidate_id
        records_by_cand_id: Dict[str, List[RawRecord]] = {}
        for r in normalized_records:
            cand_id = source_id_to_cand_id[r.record_id]
            records_by_cand_id.setdefault(cand_id, []).append(r)

        # 4. Merging & Conflict Resolution
        merger = ProfileMerger(priority_list=self.priority_list)
        canonical_profiles: List[CanonicalProfile] = []

        for cand_id, cand_recs in records_by_cand_id.items():
            # Merge records into a unified profile
            profile = merger.merge(cand_id, cand_recs)
            
            # 5. Calculate overall confidence
            profile.overall_confidence = compute_overall_confidence(profile)
            
            canonical_profiles.append(profile)

        return canonical_profiles
