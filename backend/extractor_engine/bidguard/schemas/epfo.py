"""
Schema definition for EPFO (Employees' Provident Fund Organisation)
Establishment Registration.
"""

import re

DOCUMENT_TYPE = "EPFO"

REQUIRED_FIELDS = [
    "epfo_establishment_code",
    "establishment_name",
    "address",
    "date_of_registration",
    "compliance_status",
]

# Typical EPFO establishment code shape: <state>/<region office>/<number>/<extension>
EPFO_CODE_PATTERN = re.compile(r"^[A-Z]{2}/[A-Z]{3}/\d{5,10}/\d{1,4}$")

DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")

VALID_COMPLIANCE_STATUSES = {"Compliant", "Non-Compliant"}


def normalize_code(raw_value):
    if not raw_value:
        return None
    return raw_value.strip().upper()


def is_valid_code_format(value):
    return bool(value) and bool(EPFO_CODE_PATTERN.match(value))


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
        "code_format_valid": is_valid_code_format(fields.get("epfo_establishment_code")),
        "compliance_status_recognized": status in VALID_COMPLIANCE_STATUSES if status else False,
    }
