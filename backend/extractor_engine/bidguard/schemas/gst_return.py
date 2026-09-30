"""Schema for a GST Return Filing Record."""

import re

DOCUMENT_TYPE = "GST_RETURN"

REQUIRED_FIELDS = [
    "gstin",
    "legal_name",
    "return_period",
    "return_type",
    "filing_date",
    "filing_status",
    "acknowledgement_number",
]

PAN_GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z0-9]{10}\d[A-Z]\d$")
DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def normalize_gstin(value):
    if not value:
        return None
    return re.sub(r"\s+", "", value).upper()


def normalize_date(value):
    if not value:
        return None
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value)
    if not match:
        return value.strip()
    dd, mm, yyyy = match.groups()
    return f"{int(dd):02d}/{int(mm):02d}/{yyyy}"


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    status = (fields.get("filing_status") or "").strip().lower()
    recognized = status in {
        "filed", "filed successfully", "submitted", "accepted",
        "not filed", "pending", "rejected"
    }
    compliance = (fields.get("compliance_status") or "").strip().lower()
    compliance_recognized = compliance in {
        "compliant", "non-compliant", "non compliant", "pending", "under review"
    }
    return {
        "missing_fields": missing,
        "gstin_format_valid": bool(fields.get("gstin") and PAN_GSTIN_PATTERN.match(fields["gstin"])),
        "filing_status_recognized": recognized,
        "compliance_status_recognized": compliance_recognized,
        "filing_date_format_valid": bool(fields.get("filing_date") and DATE_PATTERN.match(fields["filing_date"])),
    }
