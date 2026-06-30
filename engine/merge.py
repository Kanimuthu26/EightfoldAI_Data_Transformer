import re
from typing import List, Dict, Any, Optional, Set
from ingestion.base import RawRecord
from engine.canonical import (
    CanonicalProfile, CanonicalSkill, CanonicalExperience, CanonicalEducation, CanonicalProvenance
)
from engine.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill

# Default source authority weights for confidence calculations
SOURCE_AUTHORITY = {
    "ATS JSON": 0.95,
    "Recruiter CSV": 0.85,
    "Resume": 0.70,
    "Recruiter Notes": 0.50
}

def get_source_authority(source: str) -> float:
    return SOURCE_AUTHORITY.get(source, 0.50)

class ProfileMerger:
    def __init__(self, priority_list: List[str] = None):
        # Default priority order: higher index/earlier position is higher trust
        self.priority_list = priority_list or ["ATS JSON", "Recruiter CSV", "Resume", "Recruiter Notes"]

    def _get_priority_rank(self, source: str) -> int:
        """
        Returns a rank where smaller numbers mean higher priority.
        If source is not in the list, it gets a default low priority.
        """
        try:
            return self.priority_list.index(source)
        except ValueError:
            return len(self.priority_list)

    def merge(self, candidate_id: str, records: List[RawRecord]) -> CanonicalProfile:
        """
        Merges flat list of RawRecords belonging to the same candidate ID
        into a single unified CanonicalProfile.
        """
        profile = CanonicalProfile(candidate_id=candidate_id)
        
        # Group records by field name
        field_records: Dict[str, List[RawRecord]] = {}
        for r in records:
            field_records.setdefault(r.field, []).append(r)

        # 1. Merge Scalar Fields (full_name, headline, years_experience)
        profile.full_name = self._merge_scalar(field_records.get("full_name", []), "full_name", profile.provenance)
        profile.headline = self._merge_scalar(field_records.get("headline", []), "headline", profile.provenance)
        
        years_exp_val = self._merge_scalar(field_records.get("years_experience", []), "years_experience", profile.provenance)
        if years_exp_val is not None:
            try:
                profile.years_experience = float(years_exp_val)
            except (ValueError, TypeError):
                profile.years_experience = None

        # 2. Merge List/Array Fields (emails, phones)
        profile.emails = self._merge_emails(field_records.get("emails", []), profile.provenance)
        profile.phones = self._merge_phones(field_records.get("phones", []), profile.provenance)

        # 3. Merge Location
        profile.location = self._merge_location(field_records.get("location", []), profile.provenance)

        # 4. Merge Links
        profile.links = self._merge_links(field_records.get("links", []), profile.provenance)

        # 5. Merge Skills (unique, canonicalized, with confidence scoring)
        profile.skills = self._merge_skills(field_records.get("skills", []), profile.provenance)

        # 6. Merge Experience (deduplicated by company)
        profile.experience = self._merge_experience(field_records.get("experience", []), profile.provenance)

        # 7. Merge Education (deduplicated by institution)
        profile.education = self._merge_education(field_records.get("education", []), profile.provenance)

        return profile

    def _merge_scalar(self, records: List[RawRecord], field_name: str, provenance: List[CanonicalProvenance]) -> Any:
        if not records:
            return None
            
        # Sort by source priority rank
        sorted_records = sorted(records, key=lambda r: self._get_priority_rank(r.source))
        
        for r in sorted_records:
            if r.value is not None and str(r.value).strip() != "":
                # Add to provenance
                provenance.append(CanonicalProvenance(field=field_name, source=r.source, method=r.method))
                return r.value
                
        return None

    def _merge_emails(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> List[str]:
        emails_set = set()
        sources_seen = set()
        
        # Sort records by priority to retain order of preferred emails
        sorted_records = sorted(records, key=lambda r: self._get_priority_rank(r.source))
        
        result = []
        for r in sorted_records:
            if not r.value:
                continue
            email_clean = str(r.value).strip().lower()
            if email_clean and email_clean not in emails_set:
                emails_set.add(email_clean)
                result.append(email_clean)
                if r.source not in sources_seen:
                    sources_seen.add(r.source)
                    provenance.append(CanonicalProvenance(field="emails", source=r.source, method=r.method))
        return result

    def _merge_phones(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> List[str]:
        phones_set = set()
        sources_seen = set()
        
        sorted_records = sorted(records, key=lambda r: self._get_priority_rank(r.source))
        
        result = []
        for r in sorted_records:
            if not r.value:
                continue
            phone_norm = normalize_phone(r.value)
            if phone_norm and phone_norm not in phones_set:
                phones_set.add(phone_norm)
                result.append(phone_norm)
                if r.source not in sources_seen:
                    sources_seen.add(r.source)
                    provenance.append(CanonicalProvenance(field="phones", source=r.source, method=r.method))
        return result

    def _merge_location(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> Dict[str, Optional[str]]:
        location_out = {"city": None, "region": None, "country": None}
        if not records:
            return location_out

        # Collect parts from records by priority
        sorted_records = sorted(records, key=lambda r: self._get_priority_rank(r.source))
        
        city_rec, region_rec, country_rec = None, None, None
        
        for r in sorted_records:
            val = r.value
            if not val:
                continue
            
            # If location value is structured dict
            if isinstance(val, dict):
                city = val.get("city")
                region = val.get("region")
                country = val.get("country")
                
                if city and not location_out["city"]:
                    location_out["city"] = str(city).strip()
                    city_rec = r
                if region and not location_out["region"]:
                    location_out["region"] = str(region).strip()
                    region_rec = r
                if country and not location_out["country"]:
                    location_out["country"] = normalize_country(country)
                    country_rec = r
            # If location value is just a string (try to infer country/city)
            elif isinstance(val, str) and val.strip():
                parts = [p.strip() for p in val.split(',')]
                # Heuristic: last part is country or state
                if len(parts) == 1:
                    norm_c = normalize_country(parts[0])
                    if norm_c and len(norm_c) == 2: # ISO code
                        if not location_out["country"]:
                            location_out["country"] = norm_c
                            country_rec = r
                    else:
                        if not location_out["city"]:
                            location_out["city"] = parts[0]
                            city_rec = r
                elif len(parts) >= 2:
                    norm_c = normalize_country(parts[-1])
                    if not location_out["country"]:
                        location_out["country"] = norm_c or parts[-1]
                        country_rec = r
                    if not location_out["city"]:
                        location_out["city"] = parts[0]
                        city_rec = r
                    if len(parts) == 3 and not location_out["region"]:
                        location_out["region"] = parts[1]
                        region_rec = r

        # Register provenances
        added_sources = set()
        for rec, field_part in [(city_rec, "location.city"), (region_rec, "location.region"), (country_rec, "location.country")]:
            if rec and rec.source not in added_sources:
                added_sources.add(rec.source)
                provenance.append(CanonicalProvenance(field=field_part, source=rec.source, method=rec.method))

        return location_out

    def _merge_links(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> Dict[str, Any]:
        links_out = {"linkedin": None, "github": None, "portfolio": None, "other": []}
        
        sorted_records = sorted(records, key=lambda r: self._get_priority_rank(r.source))
        added_sources = set()
        
        for r in sorted_records:
            val = r.value
            if not val:
                continue
            
            # Can be a dict or a string URL
            if isinstance(val, dict):
                for key in ["linkedin", "github", "portfolio"]:
                    link_val = val.get(key)
                    if link_val and not links_out[key]:
                        links_out[key] = str(link_val).strip()
                        if r.source not in added_sources:
                            added_sources.add(r.source)
                            provenance.append(CanonicalProvenance(field=f"links.{key}", source=r.source, method=r.method))
                
                # Check for other links
                other_val = val.get("other", [])
                if isinstance(other_val, list):
                    for link in other_val:
                        if link and link not in links_out["other"]:
                            links_out["other"].append(str(link).strip())
            elif isinstance(val, str) and val.strip():
                url_clean = val.strip()
                if "linkedin.com" in url_clean.lower() and not links_out["linkedin"]:
                    links_out["linkedin"] = url_clean
                    provenance.append(CanonicalProvenance(field="links.linkedin", source=r.source, method=r.method))
                elif "github.com" in url_clean.lower() and not links_out["github"]:
                    links_out["github"] = url_clean
                    provenance.append(CanonicalProvenance(field="links.github", source=r.source, method=r.method))
                else:
                    if url_clean not in links_out["other"]:
                        links_out["other"].append(url_clean)

        return links_out

    def _merge_skills(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> List[CanonicalSkill]:
        # Group skill occurrences by normalized name
        skill_occurrences: Dict[str, List[RawRecord]] = {}
        for r in records:
            if not r.value:
                continue
            norm = normalize_skill(r.value)
            if norm:
                skill_occurrences.setdefault(norm, []).append(r)

        canonical_skills = []
        for skill_name, recs in skill_occurrences.items():
            # Get list of unique sources
            sources = list(set(r.source for r in recs))
            methods = list(set(r.method for r in recs))
            
            # Confidence score calculation:
            # Base confidence is the authority score of the highest priority source that mentions the skill
            highest_auth_source = max(sources, key=lambda s: get_source_authority(s))
            base_conf = get_source_authority(highest_auth_source)
            
            # Multi-source agreement boost: add 0.05 for each additional corroborating source, cap at 0.99
            agreement_boost = 0.05 * (len(sources) - 1)
            final_conf = min(base_conf + agreement_boost, 0.99)
            
            canonical_skills.append(
                CanonicalSkill(name=skill_name, confidence=final_conf, sources=sources)
            )
            
            # Log provenance
            for s in sources:
                meth = next(r.method for r in recs if r.source == s)
                provenance.append(CanonicalProvenance(field=f"skills.{skill_name}", source=s, method=meth))
                
        # Sort skills by confidence descending, then name alphabetically
        return sorted(canonical_skills, key=lambda s: (-s.confidence, s.name))

    def _normalize_company_name(self, name: Optional[str]) -> str:
        """
        Helper to normalize company names for deduplication.
        E.g. 'Google Inc.' -> 'google'
        """
        if not name:
            return ""
        name_clean = str(name).lower().strip()
        # Remove suffixes
        name_clean = re.sub(r'\b(inc|corp|corporation|llc|ltd|co|limited|systems|technologies)\b[\.]?', '', name_clean)
        # Strip non-alphanumeric
        name_clean = re.sub(r'[^a-z0-9]', '', name_clean)
        return name_clean

    def _merge_experience(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> List[CanonicalExperience]:
        # Group experience elements by normalized company name
        grouped_exp: Dict[str, List[Dict[str, Any]]] = {}
        source_records: Dict[str, List[RawRecord]] = {}

        for r in sorted(records, key=lambda x: self._get_priority_rank(x.source)):
            val = r.value
            if not isinstance(val, dict):
                continue
            
            comp = val.get("company")
            norm_comp = self._normalize_company_name(comp)
            if not norm_comp:
                norm_comp = f"unknown_{r.record_id}"

            grouped_exp.setdefault(norm_comp, []).append(val)
            source_records.setdefault(norm_comp, []).append(r)

        result_exp = []
        for norm_comp, items in grouped_exp.items():
            recs = source_records[norm_comp]
            
            # Resolve fields by priority
            company = None
            title = None
            start = None
            end = None
            summaries = []

            for item, rec in zip(items, recs):
                if item.get("company") and not company:
                    company = item.get("company")
                if item.get("title") and not title:
                    title = item.get("title")
                if item.get("start") and not start:
                    start = normalize_date(item.get("start"))
                if item.get("end") and not end:
                    end = normalize_date(item.get("end"))
                if item.get("summary") and item.get("summary") not in summaries:
                    summaries.append(item.get("summary"))

            # Log provenance for this company experience
            logged_sources = set()
            for rec in recs:
                if rec.source not in logged_sources:
                    logged_sources.add(rec.source)
                    provenance.append(CanonicalProvenance(field=f"experience.{company or norm_comp}", source=rec.source, method=rec.method))

            result_exp.append(CanonicalExperience(
                company=company or "Unknown Company",
                title=title or "Software Engineer",
                start=start,
                end=end or "Present",
                summary="\n".join(summaries) if summaries else None
            ))

        # Sort experience by end date descending (Present first, then parse dates)
        def sort_key(e: CanonicalExperience):
            if not e.end or e.end == "Present":
                return "9999-12"
            return e.end
            
        return sorted(result_exp, key=sort_key, reverse=True)

    def _normalize_school_name(self, name: Optional[str]) -> str:
        if not name:
            return ""
        name_clean = str(name).lower().strip()
        name_clean = re.sub(r'\b(university|college|institute|of|tech|technology|school|science)\b', '', name_clean)
        name_clean = re.sub(r'[^a-z0-9]', '', name_clean)
        return name_clean

    def _merge_education(self, records: List[RawRecord], provenance: List[CanonicalProvenance]) -> List[CanonicalEducation]:
        grouped_edu: Dict[str, List[Dict[str, Any]]] = {}
        source_records: Dict[str, List[RawRecord]] = {}

        for r in sorted(records, key=lambda x: self._get_priority_rank(x.source)):
            val = r.value
            if not isinstance(val, dict):
                continue
            
            inst = val.get("institution")
            norm_inst = self._normalize_school_name(inst)
            if not norm_inst:
                norm_inst = f"unknown_{r.record_id}"

            grouped_edu.setdefault(norm_inst, []).append(val)
            source_records.setdefault(norm_inst, []).append(r)

        result_edu = []
        for norm_inst, items in grouped_edu.items():
            recs = source_records[norm_inst]
            
            institution = None
            degree = None
            field_study = None
            end_year = None

            for item, rec in zip(items, recs):
                if item.get("institution") and not institution:
                    institution = item.get("institution")
                if item.get("degree") and not degree:
                    degree = item.get("degree")
                if item.get("field") and not field_study:
                    field_study = item.get("field")
                if item.get("end_year") and not end_year:
                    try:
                        # Extract 4 digit year
                        y_match = re.search(r'\b(19|20)\d{2}\b', str(item.get("end_year")))
                        if y_match:
                            end_year = int(y_match.group(0))
                        else:
                            end_year = int(item.get("end_year"))
                    except (ValueError, TypeError):
                        pass

            # Log provenance for this education entry
            logged_sources = set()
            for rec in recs:
                if rec.source not in logged_sources:
                    logged_sources.add(rec.source)
                    provenance.append(CanonicalProvenance(field=f"education.{institution or norm_inst}", source=rec.source, method=rec.method))

            result_edu.append(CanonicalEducation(
                institution=institution or "Unknown Institution",
                degree=degree,
                field=field_study,
                end_year=end_year
            ))

        # Sort education by end_year descending
        return sorted(result_edu, key=lambda e: e.end_year or 0, reverse=True)
