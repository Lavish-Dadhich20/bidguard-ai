"""Schema for Make in India / Local Content Declarations."""

import re

DOCUMENT_TYPE = "MAKE_IN_INDIA"

REQUIRED_FIELDS = [
    "bidder_name",
    "product_or_service_description",
    "local_content_percentage",
    "local_content_category",
    "country_of_origin",
    "declaration_date",
    "status",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    pct = fields.get("local_content_percentage")
    percentage_valid = isinstance(pct, (int, float)) and 0 <= pct <= 100
    pan = fields.get("pan")
    pan_valid = bool(pan) and bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan.upper()))
    gstin = fields.get("gstin")
    gstin_valid = bool(gstin) and bool(re.fullmatch(r"\d{2}[A-Z0-9]{10}\d[A-Z]\d", gstin.upper()))
    return {
        "missing_fields": missing,
        "local_content_percentage_valid": percentage_valid,
        "pan_format_valid": pan_valid,
        "gstin_format_valid": gstin_valid,
    }
