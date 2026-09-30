"""
Extractor for OEM (Original Equipment Manufacturer) Authorization Letters.
"""

import re

from extractors.base import BaseExtractor
from schemas import oem as oem_schema


class OEMExtractor(BaseExtractor):
    document_type = oem_schema.DOCUMENT_TYPE
    display_name = "OEM Authorization"

    _NEXT_LABEL = r"(?=\n\s*\d{1,2}\.\s|\n\s*Note:|\Z)"

    PATTERNS = {
        "oem_name": re.compile(
            r"1\.\s*OEM\s*/\s*Manufacturer Name\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "authorized_bidder_name": re.compile(
            r"2\.\s*Authorized Bidder\s*/\s*Dealer Name\s+(.+?)" + _NEXT_LABEL,
            re.IGNORECASE | re.DOTALL,
        ),
        "authorized_product_or_brand": re.compile(
            r"3\.\s*Authorized Product\s*/\s*Brand\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "validity_from": re.compile(
            r"4\.\s*Authorization Valid From\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
        ),
        "validity_to": re.compile(
            r"5\.\s*Authorization Valid To\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
        ),
        "authorization_letter_number": re.compile(
            r"6\.\s*Authorization Letter Number\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "date_of_issue": re.compile(
            r"7\.\s*Date of Issue\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
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
            "oem_name": raw.get("oem_name"),
            "authorized_bidder_name": raw.get("authorized_bidder_name"),
            "authorized_product_or_brand": raw.get("authorized_product_or_brand"),
            "validity": {
                "from": oem_schema.normalize_date(raw.get("validity_from")),
                "to": oem_schema.normalize_date(raw.get("validity_to")),
            },
            "authorization_letter_number": raw.get("authorization_letter_number"),
            "date_of_issue": oem_schema.normalize_date(raw.get("date_of_issue")),
        }
        return fields

    def validate(self, fields: dict) -> dict:
        return oem_schema.validate(fields)
