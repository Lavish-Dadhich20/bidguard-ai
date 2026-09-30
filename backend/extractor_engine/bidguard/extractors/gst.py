"""
Extractor for GST Registration Certificate (Form GST REG-06).

This is deterministic, regex/rule-based extraction. GST REG-06 is a
well-structured, numbered form, so an LLM is not needed here - a
maintainable set of anchored regexes is more reliable, cheaper, and
easier to unit-test.

If in future a bidder uploads a badly-formatted / inconsistent GST
document, an LLM-based fallback extractor could be added and slotted
into the same registry - but that is out of scope for this stage.
"""

import re

from extractors.base import BaseExtractor
from schemas import gst as gst_schema


class GSTExtractor(BaseExtractor):
    document_type = gst_schema.DOCUMENT_TYPE
    display_name = "GST Registration Certificate"

    # Each pattern captures the value that follows a numbered field label,
    # stopping at the next numbered label or end of that logical block.
    # re.DOTALL is not used; we operate line-by-line/section-by-section
    # via lookahead on the next "<digit>." label instead, since values can
    # legitimately span multiple lines (e.g. addresses).
    _NEXT_LABEL = r"(?=\n\s*\d{1,2}\.\s|\n\s*Note:|\Z)"

    PATTERNS = {
        "gstin": re.compile(
            r"1\.\s*GSTIN\s+([0-9A-Za-z]{15})", re.IGNORECASE
        ),
        "legal_name": re.compile(
            r"2\.\s*Legal Name\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "trade_name": re.compile(
            r"3\.\s*Trade Name\s*\(if any\)\s*(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "constitution_of_business": re.compile(
            r"4\.\s*Constitution of Business\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        # The printed form label itself wraps across two lines ("...Place of"
        # / "Business"), and because the value is a separate table cell, the
        # reconstructed text interleaves as:
        #   5. Address of Principal Place of <value line 1>
        #   Business <value line 2>
        # so we capture both value fragments (before and after the wrapped
        # "Business" label word) and join them back together.
        "principal_place_of_business": re.compile(
            r"5\.\s*Address of Principal Place of\s+(.+?)\s*\n\s*Business\s+(.+?)" + _NEXT_LABEL,
            re.IGNORECASE | re.DOTALL,
        ),
        "date_of_liability": re.compile(
            r"6\.\s*Date of Liability\s+(\d{2}[/-]\d{2}[/-]\d{4})", re.IGNORECASE
        ),
        "validity_raw": re.compile(
            r"7\.\s*Period of Validity\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "registration_type": re.compile(
            r"8\.\s*Type of Registration\s+(.+?)" + _NEXT_LABEL, re.IGNORECASE | re.DOTALL
        ),
        "approving_authority_raw": re.compile(
            r"9\.\s*Particulars of Approving Authority\s+(.+?)" + _NEXT_LABEL,
            re.IGNORECASE | re.DOTALL,
        ),
        "date_of_issue": re.compile(
            r"10\.\s*Date of Issue of Certificate\s+(\d{2}[/-]\d{2}[/-]\d{4})",
            re.IGNORECASE,
        ),
    }

    def _search(self, pattern: re.Pattern, text: str):
        match = pattern.search(text)
        if not match:
            return None
        value = " ".join(g for g in match.groups() if g)
        # Collapse internal newlines/extra whitespace from wrapped lines,
        # but keep it readable (single spaces, comma-separated where the
        # source used line breaks e.g. multi-line addresses).
        value = re.sub(r",?\s*\n\s*", ", ", value)
        value = re.sub(r"\s{2,}", " ", value)
        return value.strip(" ,")

    def _parse_validity(self, raw_value: str) -> dict:
        if not raw_value:
            return {"from": None, "to": None}
        match = re.search(
            r"From\s+(\d{2}[/-]\d{2}[/-]\d{4})\s+To\s+(.+)$",
            raw_value,
            re.IGNORECASE,
        )
        if not match:
            return {"from": None, "to": None}
        return {
            "from": gst_schema.normalize_date(match.group(1)),
            "to": gst_schema.normalize_date(match.group(2).strip()),
        }

    def _parse_approving_authority(self, raw_value: str) -> dict:
        if not raw_value:
            return {"name": None, "designation": None, "jurisdictional_office": None}

        def _grab(label):
            m = re.search(rf"{label}\s*:\s*(.+?)(?:,\s*(?:Name|Designation|Jurisdictional Office)\s*:|$)",
                           raw_value, re.IGNORECASE)
            return m.group(1).strip(" ,") if m else None

        return {
            "name": _grab("Name"),
            "designation": _grab("Designation"),
            "jurisdictional_office": _grab("Jurisdictional Office"),
        }

    def extract(self, text: str) -> dict:
        raw = {
            key: self._search(pattern, text) for key, pattern in self.PATTERNS.items()
        }

        gstin = gst_schema.normalize_gstin(raw.get("gstin"))

        fields = {
            "gstin": gstin,
            "legal_name": raw.get("legal_name"),
            "trade_name": raw.get("trade_name"),
            "constitution_of_business": raw.get("constitution_of_business"),
            "principal_place_of_business": raw.get("principal_place_of_business"),
            "date_of_liability": gst_schema.normalize_date(raw.get("date_of_liability")),
            "validity": self._parse_validity(raw.get("validity_raw")),
            "registration_type": raw.get("registration_type"),
            "approving_authority": self._parse_approving_authority(raw.get("approving_authority_raw")),
            "date_of_issue": gst_schema.normalize_date(raw.get("date_of_issue")),
        }
        return fields

    def validate(self, fields: dict) -> dict:
        return gst_schema.validate(fields)
