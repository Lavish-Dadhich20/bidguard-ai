"""
Extractor for Udyam (MSME) Registration Certificates.

Same deterministic, regex/rule-based approach as extractors/gst.py and
extractors/pan.py.
"""

import re

from extractors.base import BaseExtractor
from schemas import udyam as udyam_schema


class UdyamExtractor(BaseExtractor):
    document_type = udyam_schema.DOCUMENT_TYPE
    display_name = "Udyam / MSME Certificate"

    _NEXT_LABEL = r"(?=\n\s*\d{1,2}\.\s|\n\s*Note:|\Z)"

    PATTERNS = {
        "udyam_registration_number": re.compile(
            r"1\.\s*Udyam Registration Number\s+([A-Za-z0-9\-]+)", re.IGNORECASE
        ),
        "enterprise_name": re.compile(
            r"2\.\s*Name of Enterprise\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "type_of_organisation": re.compile(
            r"3\.\s*Type of Organisation\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "major_activity": re.compile(
            r"4\.\s*Major Activity\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "social_category": re.compile(
            r"5\.\s*Social Category\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "official_address": re.compile(
            r"6\.\s*Official Address\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "date_of_incorporation": re.compile(
            r"7\.\s*Date of Incorporation\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
        ),
        "date_of_commencement": re.compile(
            r"8\.\s*Date of Commencement of Business\s+(\d{2}[/-]\d{2}[/-]\d{4})",
            re.IGNORECASE,
        ),
        "enterprise_type": re.compile(
            r"9\.\s*Enterprise Type\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "date_of_udyam_registration": re.compile(
            r"10\.\s*Date of Udyam Registration\s+(\d{2}[/-]\d{2}[/-]\d{4})",
            re.IGNORECASE,
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
            "udyam_registration_number": udyam_schema.normalize_udyam_number(
                raw.get("udyam_registration_number")
            ),
            "enterprise_name": raw.get("enterprise_name"),
            "type_of_organisation": raw.get("type_of_organisation"),
            "major_activity": raw.get("major_activity"),
            "social_category": raw.get("social_category"),
            "official_address": raw.get("official_address"),
            "date_of_incorporation": udyam_schema.normalize_date(raw.get("date_of_incorporation")),
            "date_of_commencement": udyam_schema.normalize_date(raw.get("date_of_commencement")),
            "enterprise_type": raw.get("enterprise_type"),
            "date_of_udyam_registration": udyam_schema.normalize_date(
                raw.get("date_of_udyam_registration")
            ),
        }
        return fields

    def validate(self, fields: dict) -> dict:
        return udyam_schema.validate(fields)
