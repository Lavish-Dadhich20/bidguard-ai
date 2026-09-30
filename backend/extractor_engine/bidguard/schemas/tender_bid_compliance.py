"""Schema for a Tender / Bid Compliance Declaration."""

import re

DOCUMENT_TYPE = "TENDER_BID_COMPLIANCE"

REQUIRED_FIELDS = [
    "tender_reference",
    "tender_title",
    "bidder_name",
    "declaration_text",
    "compliance_status",
    "declaration_date",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    status = (fields.get("compliance_status") or "").strip().lower()
    recognized = status in {
        "compliant", "fully compliant", "complied",
        "non-compliant", "non compliant", "not compliant", "partially compliant",
        "complies", "does not comply"
    }
    pan = fields.get("pan")
    gstin = fields.get("gstin")
    return {
        "missing_fields": missing,
        "compliance_status_recognized": recognized,
        "pan_format_valid": bool(pan) and bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan.upper())),
        "gstin_format_valid": bool(gstin) and bool(re.fullmatch(r"\d{2}[A-Z0-9]{10}\d[A-Z]\d", gstin.upper())),
    }
