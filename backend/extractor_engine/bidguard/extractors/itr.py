"""
Extractor for Income Tax Return (ITR) Acknowledgements.
"""

import re

from extractors.base import BaseExtractor
from schemas import itr as itr_schema


class ITRExtractor(BaseExtractor):
    document_type = itr_schema.DOCUMENT_TYPE
    display_name = "Income Tax Return / ITR"

    _NEXT_LABEL = r"(?=\n\s*\d{1,2}\.\s|\n\s*Note:|\Z)"

    PATTERNS = {
        "pan": re.compile(r"1\.\s*PAN\s+([A-Za-z0-9]{10})", re.IGNORECASE),
        "assessment_year": re.compile(
            r"2\.\s*Assessment Year\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "name_of_assessee": re.compile(
            r"3\.\s*Name of Assessee\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "gross_total_income": re.compile(
            r"4\.\s*Gross Total Income\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "total_taxable_income": re.compile(
            r"5\.\s*Total Taxable Income\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "tax_paid": re.compile(
            r"6\.\s*Tax Paid\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "acknowledgement_number": re.compile(
            r"7\.\s*Acknowledgement Number\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "date_of_filing": re.compile(
            r"8\.\s*Date of Filing\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
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
            "pan": itr_schema.normalize_pan(raw.get("pan")),
            "assessment_year": raw.get("assessment_year"),
            "name_of_assessee": raw.get("name_of_assessee"),
            "gross_total_income": itr_schema.normalize_amount(raw.get("gross_total_income")),
            "total_taxable_income": itr_schema.normalize_amount(raw.get("total_taxable_income")),
            "tax_paid": itr_schema.normalize_amount(raw.get("tax_paid")),
            "acknowledgement_number": raw.get("acknowledgement_number"),
            "date_of_filing": itr_schema.normalize_date(raw.get("date_of_filing")),
        }
        return fields

    def validate(self, fields: dict) -> dict:
        return itr_schema.validate(fields)
