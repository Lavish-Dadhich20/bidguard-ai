"""
Extractor for PAN (Permanent Account Number) documents.

Supports both structured PAN records and image/scanned PAN-card OCR text.
"""

import re

from extractors.base import BaseExtractor
from schemas import pan as pan_schema


class PANExtractor(BaseExtractor):
    document_type = pan_schema.DOCUMENT_TYPE
    display_name = "PAN"

    PAN_VALUE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)

    # Structured/mock PAN record patterns.
    STRUCTURED_PATTERNS = {
        "pan_number": re.compile(
            r"(?:1\.\s*)?Permanent Account Number\s*[:\-]?\s*([A-Za-z0-9]{10})",
            re.IGNORECASE,
        ),
        "name": re.compile(
            r"(?:2\.\s*)?Name\s*[:\-]?\s*(.+?)(?=\n\s*(?:3\.|Father|Date of|4\.)|\Z)",
            re.IGNORECASE | re.DOTALL,
        ),
        "category": re.compile(
            r"(?:3\.\s*)?Category\s*[:\-]?\s*(.+?)(?=\n\s*(?:4\.|Date of|Status)|\Z)",
            re.IGNORECASE | re.DOTALL,
        ),
        "date_of_incorporation_or_birth": re.compile(
            r"Date of (?:Incorporation|Birth)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})",
            re.IGNORECASE,
        ),
        "status": re.compile(
            r"Status\s*[:\-]?\s*(.+?)(?=\n|\Z)",
            re.IGNORECASE | re.DOTALL,
        ),
    }

    def _clean(self, value):
        if not value:
            return None
        value = re.sub(r"\s+", " ", value).strip(" ,:-")
        return value or None

    def _search(self, pattern, text):
        match = pattern.search(text)
        return self._clean(match.group(1)) if match else None

    def _extract_pan_number(self, text):
        # First look for the standard PAN pattern anywhere in OCR output.
        match = self.PAN_VALUE.search(text.upper())
        if match:
            return match.group(0).upper()

        # Then use the structured-document pattern.
        return self._search(self.STRUCTURED_PATTERNS["pan_number"], text)

    def _extract_card_name(self, text):
        # OCR of a physical PAN card commonly produces:
        #   Name ...
        #   YUVRAJ SINGH CHUNDAWAT
        #   ... Father's Name ...
        # Prefer the first clean, mostly-uppercase line after the Name label.
        lines = [re.sub(r"\s+", " ", line).strip(" _-:;") for line in text.splitlines()]

        for index, line in enumerate(lines):
            lower = line.lower()
            if "father" in lower or "father's" in lower:
                continue
            if re.search(r"\bname\b", lower):
                for candidate in lines[index + 1:index + 4]:
                    if not candidate:
                        continue
                    candidate_lower = candidate.lower()
                    if any(label in candidate_lower for label in (
                        "father", "date of", "signature", "permanent account",
                    )):
                        break
                    cleaned = re.sub(r"[^A-Za-z .']", " ", candidate)
                    cleaned = re.sub(r"\s+", " ", cleaned).strip()
                    words = cleaned.split()
                    if len(words) >= 2 and sum(w.isalpha() for w in words) >= 2:
                        return cleaned.upper()

        # Fallback for structured PAN records.
        return self._search(self.STRUCTURED_PATTERNS["name"], text)

    def extract(self, text: str) -> dict:
        pan_number = self._extract_pan_number(text)

        name = self._extract_card_name(text)

        date_value = self._search(
            self.STRUCTURED_PATTERNS["date_of_incorporation_or_birth"], text
        )

        # OCR on PAN cards may return the date without the label cleanly.
        if not date_value:
            dates = re.findall(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", text)
            if dates:
                # The PAN card DOB is normally the only conventional date in
                # the OCR text. Use the first one rather than inventing data.
                date_value = dates[0]

        return {
            "pan_number": pan_schema.normalize_pan(pan_number),
            "name": name,
            "category": self._search(self.STRUCTURED_PATTERNS["category"], text),
            "date_of_incorporation_or_birth": pan_schema.normalize_date(date_value),
            "status": self._search(self.STRUCTURED_PATTERNS["status"], text),
        }

    def validate(self, fields: dict) -> dict:
        return pan_schema.validate(fields)
