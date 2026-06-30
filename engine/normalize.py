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

# Default country code for India
DEFAULT_COUNTRY_CODE = "91"

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a phone number to E.164 format (+[country_code][digits]).
    Defaults to +91 (India) for bare 10-digit numbers or numbers with a
    leading 0 (e.g. 09876543210 -> +919876543210).
    """
    if not phone:
        return None

    phone_str = str(phone).strip()
    # Strip everything except + and digits
    cleaned = re.sub(r'[^\d+]', '', phone_str)

    if not cleaned:
        return None

    # Already has explicit country code
    if cleaned.startswith('+'):
        return cleaned

    # Indian trunk prefix: leading 0 followed by 10 digits (e.g. 09876543210)
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return f"+{DEFAULT_COUNTRY_CODE}{cleaned[1:]}"

    # Bare 10-digit mobile number — assume India
    if len(cleaned) == 10:
        return f"+{DEFAULT_COUNTRY_CODE}{cleaned}"

    # 12-digit number starting with 91 — already has India code without +
    if len(cleaned) == 12 and cleaned.startswith('91'):
        return f"+{cleaned}"

    # Fallback: just prepend +
    return f"+{cleaned}"


# ---------------------------------------------------------------------------
# ITU-T E.164 country-code table: maps each calling code (as string, longest
# match wins) to the typical local subscriber number length.  The local length
# is used to split a full E.164 number into (country_code, local_number) so
# that numbers entered with or without the country code resolve to the same
# merge key.
#
# Format: { "calling_code_digits": local_subscriber_digits }
# Where local_subscriber_digits is the most common length for that country.
# ---------------------------------------------------------------------------
COUNTRY_CODE_LOCAL_LENGTHS: Dict[str, int] = {
    # 3-digit codes (checked first – longest match)
    "355": 9,   # Albania
    "213": 9,   # Algeria
    "376": 6,   # Andorra
    "244": 9,   # Angola
    "374": 8,   # Armenia
    "297": 7,   # Aruba
    "994": 9,   # Azerbaijan
    "973": 8,   # Bahrain
    "880": 10,  # Bangladesh
    "375": 9,   # Belarus
    "501": 7,   # Belize
    "229": 8,   # Benin
    "975": 8,   # Bhutan
    "591": 8,   # Bolivia
    "387": 8,   # Bosnia
    "267": 8,   # Botswana
    "246": 7,   # British Indian Ocean
    "673": 7,   # Brunei
    "226": 8,   # Burkina Faso
    "257": 8,   # Burundi
    "855": 9,   # Cambodia
    "237": 9,   # Cameroon
    "238": 7,   # Cape Verde
    "236": 8,   # Central African Republic
    "235": 8,   # Chad
    "682": 5,   # Cook Islands
    "506": 8,   # Costa Rica
    "385": 9,   # Croatia
    "357": 8,   # Cyprus
    "420": 9,   # Czech Republic
    "243": 9,   # DR Congo
    "253": 8,   # Djibouti
    "670": 8,   # East Timor
    "593": 9,   # Ecuador
    "503": 8,   # El Salvador
    "240": 9,   # Equatorial Guinea
    "291": 7,   # Eritrea
    "372": 8,   # Estonia
    "251": 9,   # Ethiopia
    "679": 7,   # Fiji
    "358": 10,  # Finland
    "241": 7,   # Gabon
    "220": 7,   # Gambia
    "995": 9,   # Georgia
    "233": 9,   # Ghana
    "350": 8,   # Gibraltar
    "299": 6,   # Greenland
    "502": 8,   # Guatemala
    "224": 9,   # Guinea
    "245": 9,   # Guinea-Bissau
    "592": 7,   # Guyana
    "509": 8,   # Haiti
    "504": 8,   # Honduras
    "852": 8,   # Hong Kong
    "354": 7,   # Iceland
    "964": 10,  # Iraq
    "972": 9,   # Israel
    "225": 10,  # Ivory Coast
    "962": 9,   # Jordan
    "254": 9,   # Kenya
    "686": 8,   # Kiribati
    "965": 8,   # Kuwait
    "996": 9,   # Kyrgyzstan
    "856": 9,   # Laos
    "371": 8,   # Latvia
    "961": 8,   # Lebanon
    "266": 8,   # Lesotho
    "231": 8,   # Liberia
    "218": 9,   # Libya
    "423": 7,   # Liechtenstein
    "370": 8,   # Lithuania
    "352": 9,   # Luxembourg
    "853": 8,   # Macao
    "261": 9,   # Madagascar
    "265": 9,   # Malawi
    "960": 7,   # Maldives
    "223": 8,   # Mali
    "356": 8,   # Malta
    "692": 7,   # Marshall Islands
    "222": 8,   # Mauritania
    "230": 8,   # Mauritius
    "691": 7,   # Micronesia
    "373": 8,   # Moldova
    "976": 8,   # Mongolia
    "382": 8,   # Montenegro
    "212": 9,   # Morocco
    "258": 9,   # Mozambique
    "264": 9,   # Namibia
    "674": 7,   # Nauru
    "977": 10,  # Nepal
    "505": 8,   # Nicaragua
    "227": 8,   # Niger
    "234": 10,  # Nigeria
    "850": 10,  # North Korea
    "389": 8,   # North Macedonia
    "968": 8,   # Oman
    "680": 7,   # Palau
    "970": 9,   # Palestine
    "507": 8,   # Panama
    "675": 8,   # Papua New Guinea
    "595": 9,   # Paraguay
    "51":  9,   # Peru
    "63":  10,  # Philippines
    "48":  9,   # Poland
    "351": 9,   # Portugal
    "974": 8,   # Qatar
    "242": 9,   # Republic of Congo
    "40":  10,  # Romania
    "250": 9,   # Rwanda
    "685": 7,   # Samoa
    "239": 7,   # Sao Tome and Principe
    "966": 9,   # Saudi Arabia
    "221": 9,   # Senegal
    "381": 9,   # Serbia
    "232": 8,   # Sierra Leone
    "421": 9,   # Slovakia
    "386": 8,   # Slovenia
    "677": 7,   # Solomon Islands
    "252": 8,   # Somalia
    "27":  9,   # South Africa
    "211": 9,   # South Sudan
    "94":  9,   # Sri Lanka
    "249": 9,   # Sudan
    "597": 7,   # Suriname
    "268": 8,   # Swaziland
    "963": 9,   # Syria
    "886": 9,   # Taiwan
    "992": 9,   # Tajikistan
    "255": 9,   # Tanzania
    "228": 8,   # Togo
    "676": 7,   # Tonga
    "868": 7,   # Trinidad and Tobago
    "216": 8,   # Tunisia
    "993": 8,   # Turkmenistan
    "688": 5,   # Tuvalu
    "256": 9,   # Uganda
    "380": 9,   # Ukraine
    "971": 9,   # UAE
    "598": 8,   # Uruguay
    "998": 9,   # Uzbekistan
    "678": 7,   # Vanuatu
    "58":  10,  # Venezuela
    "967": 9,   # Yemen
    "260": 9,   # Zambia
    "263": 9,   # Zimbabwe
    # 2-digit codes
    "20":  10,  # Egypt
    "30":  10,  # Greece
    "31":  9,   # Netherlands
    "32":  9,   # Belgium
    "33":  9,   # France
    "34":  9,   # Spain
    "36":  9,   # Hungary
    "39":  10,  # Italy
    "41":  9,   # Switzerland
    "43":  10,  # Austria
    "44":  10,  # UK
    "45":  8,   # Denmark
    "46":  9,   # Sweden
    "47":  8,   # Norway
    "49":  10,  # Germany
    "52":  10,  # Mexico
    "53":  8,   # Cuba
    "54":  10,  # Argentina
    "55":  11,  # Brazil
    "56":  9,   # Chile
    "57":  10,  # Colombia
    "60":  9,   # Malaysia
    "61":  9,   # Australia
    "62":  10,  # Indonesia
    "64":  9,   # New Zealand
    "65":  8,   # Singapore
    "66":  9,   # Thailand
    "7":   10,  # Russia/Kazakhstan
    "81":  10,  # Japan
    "82":  10,  # South Korea
    "84":  9,   # Vietnam
    "86":  11,  # China
    "90":  10,  # Turkey
    "91":  10,  # India  ← default
    "92":  10,  # Pakistan
    "93":  9,   # Afghanistan
    "95":  9,   # Myanmar
    "98":  10,  # Iran
    # 1-digit NANP (North America +1)
    "1":   10,  # USA / Canada / Caribbean
}

# Pre-sort codes longest-first so we always try the most-specific match first
_SORTED_CODES = sorted(COUNTRY_CODE_LOCAL_LENGTHS.keys(), key=len, reverse=True)


def _split_e164(e164: str):
    """
    Given a fully qualified E.164 string (starts with '+'), return
    (country_code, local_number) or (None, None) if no match is found.
    """
    digits = e164.lstrip('+')
    for code in _SORTED_CODES:
        if digits.startswith(code):
            local = digits[len(code):]
            expected_len = COUNTRY_CODE_LOCAL_LENGTHS[code]
            # Accept if the local part length is within ±1 of the expected
            # length (some countries have variable-length subscriber numbers)
            if abs(len(local) - expected_len) <= 1:
                return code, local
    return None, None


def normalize_phone_for_merge(phone: Optional[str]) -> Optional[str]:
    """
    Returns a country-code-agnostic merge key for deduplication.

    The key is  "<calling_code>:<local_subscriber_number>"  so that all
    representations of the same physical number collapse to one key:

        +919876543210   ->  "91:9876543210"
        9876543210      ->  "91:9876543210"   (defaulted to +91)
        09876543210     ->  "91:9876543210"   (trunk prefix stripped)

        +447911123456   ->  "44:7911123456"
        07911123456     ->  "44:7911123456"   (UK trunk prefix, defaulted to +44
                                               only if the user has a UK source)

        +15550192834    ->  "1:5550192834"

    If the country code cannot be identified the full E.164 string is used
    as the key so the number still deduplicates with an exact match.
    """
    e164 = normalize_phone(phone)
    if not e164:
        return None

    code, local = _split_e164(e164)
    if code and local:
        return f"{code}:{local}"

    # Unknown country code — fall back to full E.164 for exact-match dedup
    return e164

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
