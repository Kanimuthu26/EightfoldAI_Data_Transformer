import csv
import os
from typing import List
from ingestion.base import SourceAdapter, RawRecord

class CSVAdapter(SourceAdapter):
    def detect(self, filepath_or_url: str) -> bool:
        if not os.path.exists(filepath_or_url):
            return False
        return filepath_or_url.lower().endswith('.csv')

    def extract(self, filepath_or_url: str) -> List[RawRecord]:
        records = []
        if not os.path.exists(filepath_or_url):
            return records

        try:
            with open(filepath_or_url, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return records
                
                # Normalize field names to match easily (lowercase, strip whitespace)
                field_map = {name.lower().strip(): name for name in reader.fieldnames}
                
                # Check for expected keys
                name_key = next((field_map[k] for k in ['name', 'full_name', 'full name'] if k in field_map), None)
                email_key = next((field_map[k] for k in ['email', 'emails', 'email_address', 'email address'] if k in field_map), None)
                phone_key = next((field_map[k] for k in ['phone', 'phones', 'phone_number', 'phone number'] if k in field_map), None)
                company_key = next((field_map[k] for k in ['current_company', 'company', 'current company'] if k in field_map), None)
                title_key = next((field_map[k] for k in ['title', 'job_title', 'job title'] if k in field_map), None)
                
                for idx, row in enumerate(reader):
                    row_id = f"{os.path.basename(filepath_or_url)}_row_{idx}"
                    
                    # Extract fields
                    name_val = row.get(name_key).strip() if name_key and row.get(name_key) else None
                    email_val = row.get(email_key).strip() if email_key and row.get(email_key) else None
                    phone_val = row.get(phone_key).strip() if phone_key and row.get(phone_key) else None
                    company_val = row.get(company_key).strip() if company_key and row.get(company_key) else None
                    title_val = row.get(title_key).strip() if title_key and row.get(title_key) else None
                    
                    source_name = "Recruiter CSV"
                    
                    if name_val:
                        records.append(RawRecord(field="full_name", value=name_val, source=source_name, method="direct_read", record_id=row_id))
                    if email_val:
                        records.append(RawRecord(field="emails", value=email_val, source=source_name, method="direct_read", record_id=row_id))
                    if phone_val:
                        records.append(RawRecord(field="phones", value=phone_val, source=source_name, method="direct_read", record_id=row_id))
                    
                    if company_val or title_val:
                        exp_entry = {
                            "company": company_val,
                            "title": title_val,
                            "start": None,
                            "end": None,
                            "summary": "Imported from recruiter CSV"
                        }
                        records.append(RawRecord(field="experience", value=exp_entry, source=source_name, method="direct_read", record_id=row_id))
        except Exception:
            # Return empty list on failure or corruption
            return []
            
        return records
