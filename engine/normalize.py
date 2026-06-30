import re
from typing import Optional, Dict, Any

# Country synonym map to ISO-3166 alpha-2
COUNTRY_MAP = {
    "united states": "US", "usa": "US", "united states of america": "US", "u.s.a.": "US", "u.s.": "US",
    "united kingdom": "GB", "uk": "GB", "u.k.": "GB", "great britain": "GB", "england": "GB",
    "india": "IN", "ind": "IN",
    "canada": "CA", "can": "CA",
    "germany": "DE", "deutschland": "DE",
    "france": "FR",
    "australia": "AU", "aus": "AU",
    "singapore": "SG", "sgp": "SG",
    "japan": "JP", "jpn": "JP",
    "china": "CN",
    "brazil": "BR", "brasil": "BR"
}

# Skill synonym map
SKILL_MAP = {
    "js": "JavaScript", "javascript": "JavaScript", "java script": "JavaScript", "ecmascript": "JavaScript",
    "py": "Python", "python": "Python", "python3": "Python",
    "ts": "TypeScript", "typescript": "TypeScript",
    "html": "HTML", "html5": "HTML",
    "css": "CSS", "css3": "CSS",
    "aws": "AWS", "amazon web services": "AWS",
    "ml": "Machine Learning", "machinelearning": "Machine Learning", "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence", "artificial intelligence": "Artificial Intelligence",
    "go": "Go", "golang": "Go", "go lang": "Go",
    "c++": "C++", "cpp": "C++", "c plus plus": "C++",
    "c#": "C#", "csharp": "C#", "c sharp": "C#",
    "react": "React", "reactjs": "React", "react.js": "React",
    "node": "Node.js", "nodejs": "Node.js", "node.js": "Node.js",
    "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js",
    "angular": "Angular", "angularjs": "Angular",
    "docker": "Docker",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "sql": "SQL", "mysql": "MySQL", "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "nosql": "NoSQL", "mongodb": "MongoDB",
    "git": "Git", "github": "Git/GitHub"
}

# Months lookup
MONTHS = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09", "sept": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a phone number to E.164 format (+[country_code][digits]).
    If no country code, defaults to +1 (US).
    """
    if not phone:
        return None
        
    phone_str = str(phone).strip()
    # Strip everything except + and digits
    cleaned = re.sub(r'[^\d+]', '', phone_str)
    
    if not cleaned:
        return None
        
    # Check if starts with +
    if cleaned.startswith('+'):
        return cleaned
        
    # Heuristics: if length is 10, assume US/CA (+1)
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    # If it is 11 and starts with 1, prepend +
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return f"+{cleaned}"
        
    # Otherwise just return with leading +
    return f"+{cleaned}"

def normalize_date(date_val: Optional[Any]) -> Optional[str]:
    """
    Normalizes experiences/education dates to YYYY-MM.
    If the value is 'Present' (case insensitive), returns 'Present'.
    """
    if not date_val:
        return None
        
    date_str = str(date_val).strip()
    if date_str.lower() in ['present', 'current', 'now', 'active']:
        return "Present"
        
    # Format: YYYY-MM
    match_yyyy_mm = re.match(r'^(\d{4})[-/](\d{1,2})$', date_str)
    if match_yyyy_mm:
        year, month = match_yyyy_mm.groups()
        return f"{year}-{int(month):02d}"
        
    # Format: MM/YYYY or MM-YYYY
    match_mm_yyyy = re.match(r'^(\d{1,2})[-/](\d{4})$', date_str)
    if match_mm_yyyy:
        month, year = match_mm_yyyy.groups()
        return f"{year}-{int(month):02d}"
        
    # Format: Month YYYY (e.g. June 2020 or Jun 2020 or 2020 Jun)
    # Search for year
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        year = year_match.group(0)
        # Search for month keyword
        month_str = None
        for m_name in MONTHS:
            if re.search(r'\b' + re.escape(m_name) + r'\b', date_str.lower()):
                month_str = MONTHS[m_name]
                break
        if month_str:
            return f"{year}-{month_str}"
        else:
            # If only year is found, default to YYYY-01
            return f"{year}-01"
            
    # Format: just YYYY
    match_yyyy = re.match(r'^(\d{4})$', date_str)
    if match_yyyy:
        return f"{match_yyyy.group(1)}-01"
        
    return None

def normalize_country(country: Optional[str]) -> Optional[str]:
    """
    Normalizes country names/codes to ISO-3166 alpha-2 format.
    """
    if not country:
        return None
        
    country_clean = str(country).strip().lower().replace('.', '')
    # Check map
    if country_clean in COUNTRY_MAP:
        return COUNTRY_MAP[country_clean]
        
    # If already a 2-letter uppercase code, return it
    if len(country_clean) == 2 and country.isupper():
        return country
        
    return country.strip() if country else None

def normalize_skill(skill: Optional[str]) -> Optional[str]:
    """
    Normalizes a skill name based on synonym map.
    """
    if not skill:
        return None
        
    skill_clean = str(skill).strip().lower()
    if skill_clean in SKILL_MAP:
        return SKILL_MAP[skill_clean]
        
    # Return capitalized/original if not in map
    # E.g. "aws lambda" -> "AWS Lambda"
    return skill.strip()
