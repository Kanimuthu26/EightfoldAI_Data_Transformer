from typing import List, Dict, Set, Optional, Tuple, Any
from engine.normalize import normalize_phone, normalize_phone_for_merge

class MatchStrategy:
    def __init__(self):
        # Indexes for O(N) lookup
        self.email_to_cand: Dict[str, str] = {}
        self.phone_to_cand: Dict[str, str] = {}
        # Keep track of emails per candidate to enforce the absent-on-either-side rule
        self.cand_to_emails: Dict[str, Set[str]] = {}

    def resolve_candidate_id(
        self, 
        emails: List[str], 
        phones: List[str], 
        existing_profiles_by_id: Dict[str, Any] = None
    ) -> Tuple[str, bool]:
        """
        Resolves which candidate ID this record belongs to.
        Returns: (candidate_id, is_new)
        """
        # Normalize inputs for matching
        norm_emails = [e.strip().lower() for e in emails if e and e.strip()]
        norm_phones = [normalize_phone_for_merge(p) for p in phones if p]
        norm_phones = [p for p in norm_phones if p]

        # 1. Primary: Match by email (case-insensitive)
        matched_by_email = None
        for email in norm_emails:
            if email in self.email_to_cand:
                matched_by_email = self.email_to_cand[email]
                break

        if matched_by_email:
            # Re-register any new emails/phones for this candidate to index
            self._register_indexes(matched_by_email, norm_emails, norm_phones)
            return matched_by_email, False

        # 2. Fallback: Match by phone
        # "Falls back to normalized-phone match when email is absent on either side."
        matched_by_phone = None
        for phone in norm_phones:
            if phone in self.phone_to_cand:
                cand_id = self.phone_to_cand[phone]
                
                # Check if email is absent on either side:
                # - Incoming profile has no emails
                # - OR the matched candidate has no emails
                matched_cand_emails = self.cand_to_emails.get(cand_id, set())
                
                if len(norm_emails) == 0 or len(matched_cand_emails) == 0:
                    matched_by_phone = cand_id
                    break

        if matched_by_phone:
            self._register_indexes(matched_by_phone, norm_emails, norm_phones)
            return matched_by_phone, False

        # 3. No match: Stands alone. Create a new candidate ID
        import uuid
        new_cand_id = f"cand_{uuid.uuid4().hex[:10]}"
        self._register_indexes(new_cand_id, norm_emails, norm_phones)
        return new_cand_id, True

    def _register_indexes(self, cand_id: str, emails: List[str], phones: List[str]):
        if cand_id not in self.cand_to_emails:
            self.cand_to_emails[cand_id] = set()

        for email in emails:
            self.email_to_cand[email] = cand_id
            self.cand_to_emails[cand_id].add(email)

        for phone in phones:
            self.phone_to_cand[phone] = cand_id

    def reset(self):
        self.email_to_cand.clear()
        self.phone_to_cand.clear()
        self.cand_to_emails.clear()
