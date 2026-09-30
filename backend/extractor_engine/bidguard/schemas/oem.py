"""
Schema definition for OEM (Original Equipment Manufacturer) Authorization
Letters.
"""

import re

DOCUMENT_TYPE = "OEM"

REQUIRED_FIELDS = [
    "oem_name",
    "authorized_bidder_name",
    "authorized_product_or_brand",
    "validity",
    "authorization_letter_number",
    "date_of_issue",
]

DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")


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

    validity = fields.get("validity") or {}
    validity_dates_present = bool(validity.get("from")) and bool(validity.get("to"))

    return {
        "missing_fields": missing,
        "validity_dates_present": validity_dates_present,
    }
