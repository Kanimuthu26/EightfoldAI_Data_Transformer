import json
import os
from typing import List, Any, Dict
from ingestion.base import SourceAdapter, RawRecord

class ATSJsonAdapter(SourceAdapter):
    def __init__(self, mapping: Dict[str, List[str]] = None):
        # Default mapping of canonical fields to possible custom ATS fields
        self.mapping = mapping or {
            "full_name": ["candidate_name", "name", "fullName", "fullName"],
            "emails": ["primary_email", "email", "emailAddress", "emails"],
            "phones": ["cell_phone", "phone", "phoneNumber", "phones", "mobile"],
            "headline": ["headline", "tagline", "summary_title"],
            "years_experience": ["years_experience", "total_experience", "yoe"],
            "location": ["location", "address", "geo"],
            "links": ["links", "websites", "urls", "portfolio_urls"],
            "skills": ["skills", "technologies", "tags", "keywords"],
            "experience": ["experience_history", "jobs", "work_history", "experience"],
            "education": ["education_history", "schools", "academic_history", "education"]
        }

    def detect(self, filepath_or_url: str) -> bool:
        if not os.path.exists(filepath_or_url):
            return False
        return filepath_or_url.lower().endswith('.json')

    def _resolve_key(self, data: Dict[str, Any], canonical_key: str) -> Any:
        possible_keys = self.mapping.get(canonical_key, [])
        for key in possible_keys:
            if key in data:
                return data[key]
        return None

    def extract(self, filepath_or_url: str) -> List[RawRecord]:
        records = []
        if not os.path.exists(filepath_or_url):
            return records

        try:
            with open(filepath_or_url, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Could be a list of candidates or a single candidate dict
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                # Check if it's a wrapper dict, e.g. {"candidates": [...]}
                if "candidates" in data and isinstance(data["candidates"], list):
                    candidates = data["candidates"]
                else:
                    candidates = [data]
            else:
                return records

            source_name = "ATS JSON"

            for idx, candidate in enumerate(candidates):
                row_id = f"{os.path.basename(filepath_or_url)}_cand_{idx}"
                
                # Extract scalar values
                for field in ["full_name", "headline", "years_experience"]:
                    val = self._resolve_key(candidate, field)
                    if val is not None:
                        records.append(RawRecord(field=field, value=val, source=source_name, method="direct_read", record_id=row_id))
                
                # Extract emails (can be string or list)
                emails_val = self._resolve_key(candidate, "emails")
                if emails_val:
                    if isinstance(emails_val, list):
                        for e in emails_val:
                            if e: records.append(RawRecord(field="emails", value=str(e).strip(), source=source_name, method="direct_read", record_id=row_id))
                    else:
                        records.append(RawRecord(field="emails", value=str(emails_val).strip(), source=source_name, method="direct_read", record_id=row_id))

                # Extract phones (can be string or list)
                phones_val = self._resolve_key(candidate, "phones")
                if phones_val:
                    if isinstance(phones_val, list):
                        for p in phones_val:
                            if p: records.append(RawRecord(field="phones", value=str(p).strip(), source=source_name, method="direct_read", record_id=row_id))
                    else:
                        records.append(RawRecord(field="phones", value=str(phones_val).strip(), source=source_name, method="direct_read", record_id=row_id))

                # Extract location (can be dict or string)
                loc_val = self._resolve_key(candidate, "location")
                if loc_val:
                    records.append(RawRecord(field="location", value=loc_val, source=source_name, method="direct_read", record_id=row_id))

                # Extract links (can be list, dict, or string)
                links_val = self._resolve_key(candidate, "links")
                if links_val:
                    records.append(RawRecord(field="links", value=links_val, source=source_name, method="direct_read", record_id=row_id))

                # Extract skills (can be list of strings, or list of dicts)
                skills_val = self._resolve_key(candidate, "skills")
                if skills_val:
                    if isinstance(skills_val, list):
                        for s in skills_val:
                            records.append(RawRecord(field="skills", value=s, source=source_name, method="direct_read", record_id=row_id))
                    else:
                        records.append(RawRecord(field="skills", value=skills_val, source=source_name, method="direct_read", record_id=row_id))

                # Extract experience history list
                exp_val = self._resolve_key(candidate, "experience")
                if isinstance(exp_val, list):
                    for item in exp_val:
                        if isinstance(item, dict):
                            # Map sub-keys
                            company = item.get("employer") or item.get("company_name") or item.get("company")
                            title = item.get("role") or item.get("title") or item.get("job_title")
                            start = item.get("start_date") or item.get("start") or item.get("from")
                            end = item.get("end_date") or item.get("end") or item.get("to")
                            summary = item.get("description") or item.get("summary") or item.get("notes")
                            
                            exp_entry = {
                                "company": str(company).strip() if company else None,
                                "title": str(title).strip() if title else None,
                                "start": str(start).strip() if start else None,
                                "end": str(end).strip() if end else None,
                                "summary": str(summary).strip() if summary else None
                            }
                            records.append(RawRecord(field="experience", value=exp_entry, source=source_name, method="direct_read", record_id=row_id))

                # Extract education history list
                edu_val = self._resolve_key(candidate, "education")
                if isinstance(edu_val, list):
                    for item in edu_val:
                        if isinstance(item, dict):
                            institution = item.get("school") or item.get("institution") or item.get("university")
                            degree = item.get("degree") or item.get("qualification")
                            field_of_study = item.get("field_of_study") or item.get("field") or item.get("major")
                            end_year = item.get("grad_year") or item.get("end_year") or item.get("graduation_date")
                            
                            edu_entry = {
                                "institution": str(institution).strip() if institution else None,
                                "degree": str(degree).strip() if degree else None,
                                "field": str(field_of_study).strip() if field_of_study else None,
                                "end_year": end_year
                            }
                            records.append(RawRecord(field="education", value=edu_entry, source=source_name, method="direct_read", record_id=row_id))

        except Exception:
            # Failure/corruption returns empty
            return []

        return records
