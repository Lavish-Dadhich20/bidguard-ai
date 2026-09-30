"""
Schema definition for GST Registration Certificate (Form GST REG-06).

A schema module is intentionally "dumb": it only knows the shape of the
data and how to validate/normalize individual values. It does NOT know
how to read a PDF or how to locate values inside raw text. That job
belongs to the corresponding extractor in extractors/gst.py.

Every future document type (PAN, Udyam, ITR, OEM ...) should get its own
schemas/<type>.py file following the same pattern:
    - DOCUMENT_TYPE
    - FIELD_DEFINITIONS / REQUIRED_FIELDS
    - normalize_* helpers
    - validate(fields) -> validation report
"""

import re

DOCUMENT_TYPE = "GST_REG_06"

# Top-level scalar fields expected in the final JSON output.
REQUIRED_FIELDS = [
    "gstin",
    "legal_name",
    "trade_name",
    "constitution_of_business",
    "principal_place_of_business",
    "date_of_liability",
    "validity",
    "registration_type",
    "approving_authority",
    "date_of_issue",
]

# GSTIN format: 2 digit state code, 10 char PAN, 1 entity code,
# 1 checksum-ish char 'Z' by convention, 1 alphanumeric checksum.
GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

DATE_PATTERNS = [
    (re.compile(r"^(\d{2})/(\d{2})/(\d{4})$"), "%d/%m/%Y"),
    (re.compile(r"^(\d{2})-(\d{2})-(\d{4})$"), "%d-%m-%Y"),
]


def normalize_gstin(raw_value):
    """Uppercase and strip whitespace. Returns None if raw_value is falsy."""
    if not raw_value:
        return None
    return re.sub(r"\s+", "", raw_value).upper()


def is_valid_gstin_format(gstin_value):
    if not gstin_value:
        return False
    return bool(GSTIN_PATTERN.match(gstin_value))


def normalize_date(raw_value):
    """
    Best-effort date normalization to DD/MM/YYYY.
    Non-date strings like "Not Applicable" are returned unchanged.
    Returns None if raw_value is falsy.
    """
    if not raw_value:
        return None
    value = raw_value.strip()
    for pattern, _fmt in DATE_PATTERNS:
        match = pattern.match(value)
        if match:
            dd, mm, yyyy = match.groups()
            return f"{dd}/{mm}/{yyyy}"
    return value  # leave free-text values (e.g. "Not Applicable") as-is


def validate(fields: dict) -> dict:
    """
    Validate an already-extracted fields dict against the GST schema.

    This checks STRUCTURE and FORMAT only (e.g. "does this look like a
    GSTIN"). It does NOT check the value against any government database -
    that is a separate, later verification stage.
    """
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]

    gstin_value = fields.get("gstin")
    gstin_valid_format = is_valid_gstin_format(gstin_value) if gstin_value else False

    return {
        "missing_fields": missing,
        "gstin_format_valid": gstin_valid_format,
    }
