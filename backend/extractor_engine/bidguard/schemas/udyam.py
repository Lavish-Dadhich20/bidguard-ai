"""
Schema definition for Udyam (MSME) Registration Certificate.

Same pattern as schemas/gst.py and schemas/pan.py.
"""

import re

DOCUMENT_TYPE = "UDYAM"

REQUIRED_FIELDS = [
    "udyam_registration_number",
    "enterprise_name",
    "type_of_organisation",
    "major_activity",
    "social_category",
    "official_address",
    "date_of_incorporation",
    "date_of_commencement",
    "enterprise_type",
    "date_of_udyam_registration",
]

# UDYAM-<2 letter state code>-<2 digit district code>-<7 digit sequence>
UDYAM_PATTERN = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")

DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")

VALID_ENTERPRISE_TYPES = {"Micro", "Small", "Medium"}


def normalize_udyam_number(raw_value):
    if not raw_value:
        return None
    return re.sub(r"\s+", "", raw_value).upper()


def is_valid_udyam_format(value):
    if not value:
        return False
    return bool(UDYAM_PATTERN.match(value))


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
    udyam_value = fields.get("udyam_registration_number")
    udyam_valid_format = is_valid_udyam_format(udyam_value) if udyam_value else False

    enterprise_type = fields.get("enterprise_type")
    enterprise_type_recognized = enterprise_type in VALID_ENTERPRISE_TYPES if enterprise_type else False

    return {
        "missing_fields": missing,
        "udyam_format_valid": udyam_valid_format,
        "enterprise_type_recognized": enterprise_type_recognized,
    }
