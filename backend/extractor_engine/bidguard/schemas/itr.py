"""
Schema definition for Income Tax Return (ITR) Acknowledgement.

Same pattern as the other schemas/*.py files.
"""

import re

DOCUMENT_TYPE = "ITR"

REQUIRED_FIELDS = [
    "pan",
    "assessment_year",
    "name_of_assessee",
    "gross_total_income",
    "total_taxable_income",
    "tax_paid",
    "acknowledgement_number",
    "date_of_filing",
]

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
ASSESSMENT_YEAR_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")
DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")


def normalize_pan(raw_value):
    if not raw_value:
        return None
    return re.sub(r"\s+", "", raw_value).upper()


def is_valid_pan_format(value):
    return bool(value) and bool(PAN_PATTERN.match(value))


def is_valid_assessment_year(value):
    return bool(value) and bool(ASSESSMENT_YEAR_PATTERN.match(value))


def normalize_amount(raw_value):
    """
    'Rs. 82,40,000' -> 8240000 (int). Returns None if it can't be parsed
    as a number; never guesses a value.
    """
    if not raw_value:
        return None
    digits = re.sub(r"[^\d]", "", raw_value)
    if not digits:
        return None
    return int(digits)


def normalize_date(raw_value):
    if not raw_value:
        return None
    value = raw_value.strip()
    match = DATE_PATTERN.match(value)
    if match:
        dd, mm, yyyy = match.groups()
        return f"{dd}/{mm}/{yyyy}"
    return value


def validate(fields: dict) -> dict:
    missing = [name for name in REQUIRED_FIELDS if fields.get(name) in (None, "")]
    return {
        "missing_fields": missing,
        "pan_format_valid": is_valid_pan_format(fields.get("pan")),
        "assessment_year_format_valid": is_valid_assessment_year(fields.get("assessment_year")),
    }
