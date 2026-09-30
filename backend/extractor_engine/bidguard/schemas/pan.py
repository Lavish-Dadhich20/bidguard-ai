"""
Schema definition for PAN (Permanent Account Number).

Same pattern as schemas/gst.py: this file only knows the shape of the
data and how to validate/normalize it. Reading the PDF is the job of
extractors/pan.py.
"""

import re

DOCUMENT_TYPE = "PAN"

# These are the fields normally available on a physical PAN card.
# Category/status may exist in separate PAN records but are not printed on
# every PAN card, so they are optional rather than mandatory.
REQUIRED_FIELDS = [
    "pan_number",
    "name",
    "date_of_incorporation_or_birth",
]

# Standard PAN format: 5 letters, 4 digits, 1 letter.
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

DATE_PATTERN = re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$")


def normalize_pan(raw_value):
    if not raw_value:
        return None
    return re.sub(r"\s+", "", raw_value).upper()


def is_valid_pan_format(pan_value):
    if not pan_value:
        return False
    return bool(PAN_PATTERN.match(pan_value))


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
    pan_value = fields.get("pan_number")
    pan_valid_format = is_valid_pan_format(pan_value) if pan_value else False

    return {
        "missing_fields": missing,
        "pan_format_valid": pan_valid_format,
    }
