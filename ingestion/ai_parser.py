import os
import re
import time
import requests
from typing import List, Dict, Any
from ingestion.base import RawRecord

MISTRAL_API_KEY = "E4DxfgFR6oYZWLEMNmJ7tGL6FaxlauWV"
LLAMA_PARSE_API_KEY = "llx-5e49pnYDRtIbK5zgQJvgIoFff24r0cjleNpG6dbG4R6m6t1B"

def parse_pdf_with_llama_parse(filepath: str) -> str:
    """
    Uploads a PDF to LlamaParse and polls for the markdown text.
    """
    if not LLAMA_PARSE_API_KEY:
        return ""
        
    try:
        # 1. Upload the file
        upload_url = "https://api.cloud.llamaindex.ai/api/v1/beta/files"
        headers = {"Authorization": f"Bearer {LLAMA_PARSE_API_KEY}"}
        
        with open(filepath, "rb") as f:
            files = {"file": f}
            data = {"purpose": "parse"}
            response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=30)
            
        if response.status_code != 200:
            return ""
            
        file_id = response.json().get("id")
        if not file_id:
            return ""
            
        # 2. Trigger the parsing job
        parse_url = "https://api.cloud.llamaindex.ai/api/v2/parse"
        payload = {
            "file_id": file_id,
            "tier": "agentic",
            "version": "latest"
        }
        response = requests.post(parse_url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return ""
            
        job_id = response.json().get("id")
        if not job_id:
            return ""
            
        # 3. Poll for the result
        result_url = f"https://api.cloud.llamaindex.ai/api/v2/parse/{job_id}"
        for _ in range(30):  # Poll up to 30 times (60 seconds)
            time.sleep(2)
            res = requests.get(result_url, headers=headers, timeout=15)
            if res.status_code == 200:
                job_data = res.json()
                status = job_data.get("status")
                if status == "SUCCESS":
                    # Extract markdown text from pages
                    pages = job_data.get("markdown", {}).get("pages", [])
                    return "\n".join(p.get("markdown", "") for p in pages)
                elif status == "FAILED":
                    break
        return ""
    except Exception:
        return ""

def extract_structured_data_with_mistral(text: str, source_name: str, record_id: str) -> List[RawRecord]:
    """
    Sends the raw text to Mistral AI to extract structured candidate profile records.
    """
    if not MISTRAL_API_KEY or not text.strip():
        return []

    system_prompt = (
        "You are an expert candidate resume and recruiter notes data extractor.\n"
        "Analyze the provided text and extract candidate profile details.\n"
        "Your output MUST be a JSON list of records, where each record has exactly these keys:\n"
        "- 'field': one of 'full_name', 'emails', 'phones', 'location', 'links', 'headline', 'years_experience', 'skills', 'experience', 'education'\n"
        "- 'value': the extracted value conforming to the following schemas:\n"
        "  - 'full_name': string (the candidate's name)\n"
        "  - 'emails': string (single email address)\n"
        "  - 'phones': string (single phone number)\n"
        "  - 'location': dict with keys 'city', 'region', 'country'\n"
        "  - 'links': dict with keys 'linkedin', 'github', 'portfolio', 'other' (list of other URLs)\n"
        "  - 'headline': string\n"
        "  - 'years_experience': number (total years of experience)\n"
        "  - 'skills': string (a single skill name, e.g. 'Python')\n"
        "  - 'experience': dict with keys 'company', 'title', 'start' (YYYY-MM), 'end' (YYYY-MM or 'Present'), 'summary'\n"
        "  - 'education': dict with keys 'institution', 'degree', 'field', 'end_year' (number)\n"
        "\n"
        "Rules:\n"
        "1. Do not invent any information. If a field is missing, do not include a record for it.\n"
        "2. Keep experience summaries brief and concise.\n"
        "3. Output ONLY valid JSON. No markdown, no explanations."
    )

    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-small-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract details from this text:\n\n{text}"}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return []

        content = response.json()["choices"][0]["message"]["content"]
        # Parse the JSON response
        import json
        data = json.loads(content)
        
        # The response might be {"records": [...]} or just a list. Let's handle both.
        records_list = []
        if isinstance(data, list):
            records_list = data
        elif isinstance(data, dict):
            # Check if there is a list inside
            for key, val in data.items():
                if isinstance(val, list):
                    records_list = val
                    break
            if not records_list:
                # Treat the dict itself as a single record or try to find a list
                records_list = [data]

        raw_records = []
        for item in records_list:
            field = item.get("field")
            value = item.get("value")
            if field and value is not None:
                raw_records.append(RawRecord(
                    field=field,
                    value=value,
                    source=source_name,
                    method="ai_extraction",
                    record_id=record_id
                ))
        return raw_records
    except Exception as e:
        print(f"Mistral extraction error: {e}")
        return []
