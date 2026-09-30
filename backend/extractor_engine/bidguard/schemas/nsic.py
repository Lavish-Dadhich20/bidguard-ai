"""Schema for an NSIC Registration Certificate."""

import re

DOCUMENT_TYPE = "NSIC"

REQUIRED_FIELDS = [
    "registration_number",
    "enterprise_name",
    "pan",
    "udyam_number",
    "validity_from",
    "validity_to",
    "certificate_category",
    "status",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    return {
        "missing_fields": missing,
        "pan_format_valid": _pan_valid(fields.get("pan")),
    }


def _pan_valid(value):
    return bool(value) and bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", value.upper()))
