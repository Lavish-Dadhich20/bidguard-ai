"""
Extractor for ESIC (Employees' State Insurance Corporation) Registration
Certificates.
"""

import re

from extractors.base import BaseExtractor
from schemas import esic as esic_schema


class ESICExtractor(BaseExtractor):
    document_type = esic_schema.DOCUMENT_TYPE
    display_name = "ESIC"

    _NEXT_LABEL = r"(?=\n\s*\d{1,2}\.\s|\n\s*Note:|\Z)"

    PATTERNS = {
        "esic_registration_number": re.compile(
            r"1\.\s*ESIC Registration Number\s+(\d+)", re.IGNORECASE
        ),
        "establishment_name": re.compile(
            r"2\.\s*Establishment Name\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "address": re.compile(
            r"3\.\s*Address\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "date_of_registration": re.compile(
            r"4\.\s*Date of Registration\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
        ),
        "compliance_status": re.compile(
            r"5\.\s*Compliance Status\s+([^\n]+)", re.IGNORECASE
        ),
    }

    def _search(self, pattern: re.Pattern, text: str):
        match = pattern.search(text)
        if not match:
            return None
        value = " ".join(g for g in match.groups() if g)
        value = re.sub(r",?\s*\n\s*", ", ", value)
        value = re.sub(r"\s{2,}", " ", value)
        return value.strip(" ,")

    def extract(self, text: str) -> dict:
        raw = {key: self._search(pattern, text) for key, pattern in self.PATTERNS.items()}

        fields = {
            "esic_registration_number": esic_schema.normalize_number(raw.get("esic_registration_number")),
            "establishment_name": raw.get("establishment_name"),
            "address": raw.get("address"),
            "date_of_registration": esic_schema.normalize_date(raw.get("date_of_registration")),
            "compliance_status": raw.get("compliance_status"),
        }
        return fields

    def validate(self, fields: dict) -> dict:
        return esic_schema.validate(fields)
