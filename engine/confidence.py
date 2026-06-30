from typing import List, Dict, Any
from engine.canonical import CanonicalProfile
from engine.merge import get_source_authority

# Field weights for overall confidence (total sum = 1.0)
FIELD_WEIGHTS = {
    "emails": 0.30,
    "phones": 0.25,
    "full_name": 0.15,
    "experience": 0.10,
    "education": 0.10,
    "skills": 0.05,
    "location": 0.05
}

def calculate_field_confidence(sources: List[str]) -> float:
    """
    Computes a field's confidence based on the maximum authority of its sources,
    with a boost (+0.05 per source) for multiple corroborating sources, capped at 0.99.
    """
    if not sources:
        return 0.0
    
    unique_sources = list(set(sources))
    base_auth = max(get_source_authority(s) for s in unique_sources)
    boost = 0.05 * (len(unique_sources) - 1)
    return min(base_auth + boost, 0.99)

def compute_overall_confidence(profile: CanonicalProfile) -> float:
    """
    Computes the overall confidence of the candidate profile as a weighted average
    across all populated fields, weighted toward identity fields.
    """
    weighted_sum = 0.0
    total_weight = 0.0

    # 1. full_name
    name_sources = [p.source for p in profile.provenance if p.field == "full_name"]
    if profile.full_name and name_sources:
        weight = FIELD_WEIGHTS["full_name"]
        conf = calculate_field_confidence(name_sources)
        weighted_sum += weight * conf
        total_weight += weight

    # 2. emails
    email_sources = [p.source for p in profile.provenance if p.field == "emails"]
    if profile.emails and email_sources:
        weight = FIELD_WEIGHTS["emails"]
        conf = calculate_field_confidence(email_sources)
        weighted_sum += weight * conf
        total_weight += weight

    # 3. phones
    phone_sources = [p.source for p in profile.provenance if p.field == "phones"]
    if profile.phones and phone_sources:
        weight = FIELD_WEIGHTS["phones"]
        conf = calculate_field_confidence(phone_sources)
        weighted_sum += weight * conf
        total_weight += weight

    # 4. location
    loc_sources = [p.source for p in profile.provenance if p.field.startswith("location")]
    if any(profile.location.values()) and loc_sources:
        weight = FIELD_WEIGHTS["location"]
        conf = calculate_field_confidence(loc_sources)
        weighted_sum += weight * conf
        total_weight += weight

    # 5. skills
    skill_sources = [p.source for p in profile.provenance if p.field.startswith("skills")]
    if profile.skills and skill_sources:
        weight = FIELD_WEIGHTS["skills"]
        # Skills have individual confidence values. Let's average them.
        avg_skill_conf = sum(s.confidence for s in profile.skills) / len(profile.skills)
        weighted_sum += weight * avg_skill_conf
        total_weight += weight

    # 6. experience
    exp_sources = [p.source for p in profile.provenance if p.field.startswith("experience")]
    if profile.experience and exp_sources:
        weight = FIELD_WEIGHTS["experience"]
        conf = calculate_field_confidence(exp_sources)
        weighted_sum += weight * conf
        total_weight += weight

    # 7. education
    edu_sources = [p.source for p in profile.provenance if p.field.startswith("education")]
    if profile.education and edu_sources:
        weight = FIELD_WEIGHTS["education"]
        conf = calculate_field_confidence(edu_sources)
        weighted_sum += weight * conf
        total_weight += weight

    if total_weight == 0.0:
        return 0.0
        
    return weighted_sum / total_weight
