import os
import re
from typing import List
from ingestion.base import SourceAdapter, RawRecord

class NotesAdapter(SourceAdapter):
    def detect(self, filepath_or_url: str) -> bool:
        if not os.path.exists(filepath_or_url):
            return False
        return filepath_or_url.lower().endswith('.txt')

    def extract(self, filepath_or_url: str) -> List[RawRecord]:
        records = []
        if not os.path.exists(filepath_or_url):
            return records

        try:
            with open(filepath_or_url, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception:
            return records

        if not text.strip():
            return records

        source_name = "Recruiter Notes"
        record_id = os.path.basename(filepath_or_url)

        # 1. Try AI-based extraction using Mistral
        try:
            from ingestion.ai_parser import extract_structured_data_with_mistral
            ai_records = extract_structured_data_with_mistral(text, source_name, record_id)
            if ai_records:
                return ai_records
        except Exception:
            pass

        # 2. Fallback to regex extraction
        method_name = "regex_extraction"

        # 1. Extract Name
        # Look for labels like "Name:", "Candidate:", "Candidate Name:"
        name_match = re.search(r'\b(?:candidate\s+)?name\s*:\s*([^\n\r]+)', text, re.IGNORECASE)
        name = None
        if name_match:
            name = name_match.group(1).strip()
        else:
            # Fallback to first line if it's short and doesn't look like a header
            first_line = text.split('\n')[0].strip()
            if len(first_line) > 2 and len(first_line) < 40 and ":" not in first_line:
                name = first_line
        
        if name:
            records.append(RawRecord(field="full_name", value=name, source=source_name, method=method_name, record_id=record_id))

        # 2. Extract Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in list(set(emails)):
            records.append(RawRecord(field="emails", value=email, source=source_name, method=method_name, record_id=record_id))

        # 3. Extract Phones
        phone_pattern = r'\+?\b\d[\d\-\(\)\s\.]{7,16}\d\b'
        phones = re.findall(phone_pattern, text)
        valid_phones = []
        for p in phones:
            digits = re.sub(r'\D', '', p)
            if len(digits) >= 9 and len(digits) <= 15:
                valid_phones.append(p.strip())
        for phone in list(set(valid_phones)):
            records.append(RawRecord(field="phones", value=phone, source=source_name, method=method_name, record_id=record_id))

        # 4. Extract Skills
        # Scan for common technology keywords in a case-insensitive way
        common_skills = [
            "python", "javascript", "js", "typescript", "ts", "java", "c++", "c#", "golang", "go",
            "rust", "ruby", "php", "sql", "react", "angular", "vue", "node", "aws", "docker", "kubernetes",
            "machine learning", "ml", "deep learning", "ai", "django", "flask", "spring", "html", "css"
        ]
        
        found_skills = []
        for skill in common_skills:
            # Match word boundaries to prevent matching sub-strings (e.g. "go" in "good")
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill)
                
        for skill in found_skills:
            records.append(RawRecord(field="skills", value=skill, source=source_name, method=method_name, record_id=record_id))

        # 5. Extract Headline (if available, e.g. "Headline: Senior Software Engineer")
        headline_match = re.search(r'\b(?:headline|role|position)\s*:\s*([^\n\r]+)', text, re.IGNORECASE)
        if headline_match:
            records.append(RawRecord(field="headline", value=headline_match.group(1).strip(), source=source_name, method=method_name, record_id=record_id))

        # 6. Extract experience (e.g. "Experience: 5 years" or company mentions)
        yoe_match = re.search(r'(\d+)\+?\s*years?\s+of?\s+(?:work\s+)?experience', text, re.IGNORECASE)
        if yoe_match:
            records.append(RawRecord(field="years_experience", value=float(yoe_match.group(1)), source=source_name, method=method_name, record_id=record_id))

        # Check for company references in experience notes, e.g. "Worked at X as Y"
        job_matches = re.finditer(r'(?:worked|employed|engineer|developer)\s+at\s+([A-Za-z0-9\s]+?)(?:\s+as\s+([A-Za-z0-9\s]+?))?\s*(?:\bfor\b\s*(\d+)\s*(?:years|months))?[\.\n]', text, re.IGNORECASE)
        for jm in job_matches:
            company = jm.group(1).strip()
            title = jm.group(2).strip() if jm.group(2) else "Software Engineer"
            
            # Simple cleanup of matched strings
            company = re.sub(r'\b(?:in|on|for|during)\b.*', '', company).strip()
            title = re.sub(r'\b(?:in|on|for|during)\b.*', '', title).strip()
            
            exp_entry = {
                "company": company,
                "title": title,
                "start": None,
                "end": None,
                "summary": f"Inferred from notes: {jm.group(0).strip()}"
            }
            records.append(RawRecord(field="experience", value=exp_entry, source=source_name, method="inference", record_id=record_id))

        return records
