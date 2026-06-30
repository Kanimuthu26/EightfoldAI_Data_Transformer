import abc
from dataclasses import dataclass
from typing import Any, List

@dataclass
class RawRecord:
    field: str
    value: Any
    source: str
    method: str
    record_id: str  # Used to group raw records from the same candidate source entity (e.g. CSV row, PDF file)

class SourceAdapter(abc.ABC):
    @abc.abstractmethod
    def detect(self, filepath_or_url: str) -> bool:
        """
        Returns True if this adapter can handle the given filepath or URL.
        """
        pass

    @abc.abstractmethod
    def extract(self, filepath_or_url: str) -> List[RawRecord]:
        """
        Extracts candidate data from the filepath/URL and returns a list of RawRecords.
        Returns an empty list if the file is empty, corrupted, or missing.
        """
        pass
