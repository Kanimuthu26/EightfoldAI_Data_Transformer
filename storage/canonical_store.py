import threading
from typing import List, Dict, Optional
from engine.canonical import CanonicalProfile

class CanonicalStore:
    def __init__(self):
        self._profiles: Dict[str, CanonicalProfile] = {}
        self._lock = threading.Lock()

    def save_profile(self, profile: CanonicalProfile):
        with self._lock:
            self._profiles[profile.candidate_id] = profile

    def save_all(self, profiles: List[CanonicalProfile]):
        with self._lock:
            for p in profiles:
                self._profiles[p.candidate_id] = p

    def get_profile(self, candidate_id: str) -> Optional[CanonicalProfile]:
        with self._lock:
            return self._profiles.get(candidate_id)

    def list_profiles(self) -> List[CanonicalProfile]:
        with self._lock:
            return list(self._profiles.values())

    def clear(self):
        with self._lock:
            self._profiles.clear()

# Global singleton store
store = CanonicalStore()
