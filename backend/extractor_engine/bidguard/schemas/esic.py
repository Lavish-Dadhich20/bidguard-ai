"""
Schema definition for ESIC (Employees' State Insurance Corporation)
Registration Certificate.
"""

import re

DOCUMENT_TYPE = "ESIC"

REQUIRED_FIELDS = [
    "esic_registration_number",
    "establishment_name",
    "address",
    "date_of_registration",
    "compliance_status",
]

# ESIC employer code is conventionally a 17-digit number.
ESIC_NUMBER_PATTERN = re.compile(r"^\d{17}$")

DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")

VALID_COMPLIANCE_STATUSES = {"Compliant", "Non-Compliant"}


def normalize_number(raw_value):
    if not raw_value:
        return None
    return re.sub(r"\s+", "", raw_value)


def is_valid_number_format(value):
    return bool(value) and bool(ESIC_NUMBER_PATTERN.match(value))


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
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
    status = fields.get("compliance_status")

    return {
        "missing_fields": missing,
        "number_format_valid": is_valid_number_format(fields.get("esic_registration_number")),
        "compliance_status_recognized": status in VALID_COMPLIANCE_STATUSES if status else False,
    }
