from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class CanonicalSkill:
    name: str
    confidence: float
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "confidence": round(self.confidence, 2),
            "sources": sorted(list(set(self.sources)))
        }

@dataclass
class CanonicalExperience:
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None  # YYYY-MM
    end: Optional[str] = None    # YYYY-MM or "Present"
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "summary": self.summary
        }

@dataclass
class CanonicalEducation:
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution": self.institution,
            "degree": self.degree,
            "field": self.field,
            "end_year": self.end_year
        }

@dataclass
class CanonicalProvenance:
    field: str
    source: str
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "source": self.source,
            "method": self.method
        }

@dataclass
class CanonicalProfile:
    candidate_id: str
    full_name: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    location: Dict[str, Optional[str]] = field(default_factory=lambda: {"city": None, "region": None, "country": None})
    links: Dict[str, Any] = field(default_factory=lambda: {"linkedin": None, "github": None, "portfolio": None, "other": []})
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[CanonicalSkill] = field(default_factory=list)
    experience: List[CanonicalExperience] = field(default_factory=list)
    education: List[CanonicalEducation] = field(default_factory=list)
    provenance: List[CanonicalProvenance] = field(default_factory=list)
    overall_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "full_name": self.full_name,
            "emails": self.emails,
            "phones": self.phones,
            "location": self.location,
            "links": self.links,
            "headline": self.headline,
            "years_experience": self.years_experience,
            "skills": [s.to_dict() for s in self.skills],
            "experience": [e.to_dict() for e in self.experience],
            "education": [ed.to_dict() for ed in self.education],
            "provenance": [p.to_dict() for p in self.provenance],
            "overall_confidence": round(self.overall_confidence, 2)
        }
