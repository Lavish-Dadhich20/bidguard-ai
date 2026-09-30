"""Schema for a Certificate of Incorporation / Business Registration Certificate."""

import re

DOCUMENT_TYPE = "INCORPORATION"

REQUIRED_FIELDS = [
    "cin_or_registration_number",
    "legal_name",
    "company_type",
    "date_of_incorporation",
    "company_status",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    pan = fields.get("pan")
    return {
        "missing_fields": missing,
        "cin_present": bool(fields.get("cin_or_registration_number")),
        "company_status_present": bool(fields.get("company_status")),
        "pan_format_valid": bool(pan) and bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan.upper())),
    }
